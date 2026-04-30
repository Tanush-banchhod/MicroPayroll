"""Payroll runs router — create draft run, list runs, approve, payslip PDF, bank CSV.

When a run is created, the engine reads attendance data from the DB for the
given month/year, calculates salary for every active employee, and persists
the line items with a full snapshot for audit trail.
"""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.attendance import AttendanceLog, AttendanceStatus
from api.models.company import Company
from api.models.employee import Employee
from api.models.payroll import PayrollLineItem, PayrollRun, PayrollRunStatus
from api.schemas.payroll_run import PayrollRunCreate, PayrollRunDetail, PayrollRunResponse
from api.services.pdf import render_payslip_pdf
from api.services.bank_export import build_bank_csv
from engine.compliance.india import load_rules
from engine.salary import EmployeeInput, calculate

router = APIRouter(prefix="/api/payroll/runs", tags=["payroll-runs"])


async def _get_run_or_404(run_id: uuid.UUID, db: AsyncSession) -> PayrollRun:
    result = await db.execute(select(PayrollRun).where(PayrollRun.id == run_id))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payroll run not found")
    return run


@router.post(
    "",
    response_model=PayrollRunDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Create a draft payroll run for a company + month",
    description=(
        "Reads attendance for the given month from the DB, runs the salary engine "
        "for every active employee, and saves results as line items. "
        "Status starts as 'draft' — call /approve to finalise."
    ),
)
async def create_payroll_run(
    payload: PayrollRunCreate,
    db: AsyncSession = Depends(get_db),
) -> PayrollRunDetail:
    # Verify company exists and grab its state for compliance rules
    comp_result = await db.execute(select(Company).where(Company.id == payload.company_id))
    company = comp_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Prevent duplicate draft for the same month
    dup = await db.execute(
        select(PayrollRun).where(
            and_(
                PayrollRun.company_id == payload.company_id,
                PayrollRun.month == payload.month,
                PayrollRun.year == payload.year,
            )
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A payroll run for {payload.month}/{payload.year} already exists for this company.",
        )

    # Load compliance rules for the company's state (falls back to Maharashtra)
    rules = load_rules(company.state)

    # Fetch all active employees
    emp_result = await db.execute(
        select(Employee).where(
            and_(Employee.company_id == payload.company_id, Employee.is_active.is_(True))
        )
    )
    employees = emp_result.scalars().all()

    if not employees:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No active employees found for this company.",
        )

    # Fetch attendance logs for the month for all employees
    emp_ids = [e.id for e in employees]
    log_result = await db.execute(
        select(AttendanceLog).where(
            and_(
                AttendanceLog.employee_id.in_(emp_ids),
                func.extract("year", AttendanceLog.date) == payload.year,
                func.extract("month", AttendanceLog.date) == payload.month,
            )
        )
    )
    all_logs = log_result.scalars().all()

    # Group logs by employee id
    logs_by_employee: dict[uuid.UUID, list[AttendanceLog]] = {e.id: [] for e in employees}
    for log in all_logs:
        logs_by_employee[log.employee_id].append(log)

    # Create the payroll run record
    run = PayrollRun(
        id=uuid.uuid4(),
        company_id=payload.company_id,
        month=payload.month,
        year=payload.year,
        status=PayrollRunStatus.draft,
        run_at=datetime.now(tz=timezone.utc),
    )
    db.add(run)

    # Calculate salary for each employee and create line items
    line_items: list[PayrollLineItem] = []
    total_payout = 0.0

    for emp in employees:
        emp_logs = logs_by_employee[emp.id]
        days_present = sum(1 for l in emp_logs if l.status == AttendanceStatus.present)
        # Half-day counts as 0.5 present days
        days_present += sum(0.5 for l in emp_logs if l.status == AttendanceStatus.half_day)
        total_ot_hours = sum(l.overtime_hours or 0.0 for l in emp_logs)

        inp = EmployeeInput(
            employee_id=str(emp.id),
            base_salary=emp.base_salary,
            working_days=int(days_present),
            overtime_hours=total_ot_hours,
            unpaid_leave_days=0,  # manual attendance doesn't track unpaid leave separately yet
            festival_bonus=False,
            state=company.state,
        )
        result = calculate(inp, rules)

        item = PayrollLineItem(
            id=uuid.uuid4(),
            run_id=run.id,
            employee_id=emp.id,
            basic=result.basic,
            overtime_pay=result.overtime_pay,
            leave_deduction=result.leave_deduction,
            festival_bonus=result.festival_bonus_amount,
            gross=result.gross,
            pf_employee=result.pf_employee,
            esic_employee=result.esic_employee,
            professional_tax=result.professional_tax,
            total_deductions=result.total_deductions,
            net_pay=result.net_pay,
            snapshot=result.breakdown,
        )
        db.add(item)
        line_items.append(item)
        total_payout += result.net_pay

    run.total_payout = round(total_payout, 2)
    await db.commit()
    await db.refresh(run)
    for item in line_items:
        await db.refresh(item)

    return PayrollRunDetail.model_validate(
        {**run.__dict__, "line_items": line_items}
    )


@router.get(
    "",
    response_model=list[PayrollRunResponse],
    summary="List payroll runs for a company",
)
async def list_payroll_runs(
    company_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> list[PayrollRunResponse]:
    result = await db.execute(
        select(PayrollRun)
        .where(PayrollRun.company_id == company_id)
        .order_by(PayrollRun.year.desc(), PayrollRun.month.desc())
    )
    return [PayrollRunResponse.model_validate(r) for r in result.scalars().all()]


@router.get(
    "/{run_id}",
    response_model=PayrollRunDetail,
    summary="Get a payroll run with all line items",
)
async def get_payroll_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PayrollRunDetail:
    run = await _get_run_or_404(run_id, db)

    items_result = await db.execute(
        select(PayrollLineItem).where(PayrollLineItem.run_id == run_id)
    )
    items = items_result.scalars().all()
    return PayrollRunDetail.model_validate({**run.__dict__, "line_items": items})


@router.patch(
    "/{run_id}/approve",
    response_model=PayrollRunResponse,
    summary="Approve a draft payroll run",
)
async def approve_payroll_run(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> PayrollRunResponse:
    run = await _get_run_or_404(run_id, db)

    if run.status != PayrollRunStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Run is already '{run.status}' — only draft runs can be approved.",
        )

    run.status = PayrollRunStatus.approved
    await db.commit()
    await db.refresh(run)
    return PayrollRunResponse.model_validate(run)


@router.get(
    "/{run_id}/payslip/{employee_id}",
    summary="Download payslip PDF for one employee",
    description=(
        "Generates a professional payslip PDF for the given employee in the given "
        "payroll run. Returns a PDF file as a streaming download."
    ),
    responses={200: {"content": {"application/pdf": {}}}},
)
async def get_payslip_pdf(
    run_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    run = await _get_run_or_404(run_id, db)

    # Load company
    comp_result = await db.execute(select(Company).where(Company.id == run.company_id))
    company = comp_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")

    # Load employee
    emp_result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = emp_result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Load line item for this employee in this run
    item_result = await db.execute(
        select(PayrollLineItem).where(
            and_(
                PayrollLineItem.run_id == run_id,
                PayrollLineItem.employee_id == employee_id,
            )
        )
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payroll line item found for this employee in this run.",
        )

    pdf_bytes = render_payslip_pdf(
        company=company,
        employee=employee,
        item=item,
        run_id=str(run_id),
        month=run.month,
        year=run.year,
    )

    import calendar
    filename = (
        f"payslip_{employee.name.replace(' ', '_')}_{calendar.month_abbr[run.month]}{run.year}.pdf"
    )
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{run_id}/bank-export",
    summary="Download NEFT bulk payment CSV for a payroll run",
    description=(
        "Generates a bank-ready CSV with one row per employee: "
        "Name, Account Number, IFSC Code, Net Pay, Remarks. "
        "Compatible with NEFT bulk upload formats used by major Indian banks."
    ),
    responses={200: {"content": {"text/csv": {}}}},
)
async def get_bank_export(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    run = await _get_run_or_404(run_id, db)

    # Load all line items for the run
    items_result = await db.execute(
        select(PayrollLineItem).where(PayrollLineItem.run_id == run_id)
    )
    line_items = items_result.scalars().all()

    if not line_items:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No line items found for this payroll run.",
        )

    # Load all relevant employees in one query
    emp_ids = [item.employee_id for item in line_items]
    emps_result = await db.execute(select(Employee).where(Employee.id.in_(emp_ids)))
    employees_by_id = {str(emp.id): emp for emp in emps_result.scalars().all()}

    csv_content = build_bank_csv(
        employees_by_id=employees_by_id,
        line_items=line_items,
        month=run.month,
        year=run.year,
    )

    import calendar
    filename = f"bank_transfer_{calendar.month_abbr[run.month]}{run.year}.csv"
    return StreamingResponse(
        iter([csv_content.encode("utf-8")]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
