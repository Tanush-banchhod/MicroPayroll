"""Attendance router — manual marking and monthly grid view."""

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.attendance import AttendanceLog, AttendanceSource, AttendanceStatus
from api.models.employee import Employee
from api.schemas.attendance import (
    AttendanceManualCreate,
    AttendanceResponse,
    MonthlyAttendanceResponse,
)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.post(
    "/manual",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Manually mark attendance for an employee",
)
async def mark_attendance_manual(
    payload: AttendanceManualCreate,
    db: AsyncSession = Depends(get_db),
) -> AttendanceResponse:
    # Verify employee exists
    emp_result = await db.execute(select(Employee).where(Employee.id == payload.employee_id))
    if not emp_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    # Prevent duplicate entry for same employee + date
    dup_result = await db.execute(
        select(AttendanceLog).where(
            and_(
                AttendanceLog.employee_id == payload.employee_id,
                AttendanceLog.date == payload.date,
            )
        )
    )
    if dup_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attendance for {payload.date} already exists for this employee. Use PATCH to update.",
        )

    hours_worked: float | None = None
    if payload.punch_in and payload.punch_out:
        delta = payload.punch_out - payload.punch_in
        hours_worked = round(delta.total_seconds() / 3600, 2)

    log = AttendanceLog(
        id=uuid.uuid4(),
        employee_id=payload.employee_id,
        date=payload.date,
        status=payload.status,
        source=AttendanceSource.manual,
        punch_in=payload.punch_in,
        punch_out=payload.punch_out,
        hours_worked=hours_worked,
        overtime_hours=payload.overtime_hours,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return AttendanceResponse.model_validate(log)


@router.get(
    "/{year}/{month}",
    response_model=list[MonthlyAttendanceResponse],
    summary="Monthly attendance grid for all employees of a company",
)
async def get_monthly_attendance(
    year: int,
    month: int,
    company_id: uuid.UUID = Query(..., description="Company ID"),
    db: AsyncSession = Depends(get_db),
) -> list[MonthlyAttendanceResponse]:
    if not (1 <= month <= 12):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Month must be 1–12")

    # Get all active employees for the company
    emp_result = await db.execute(
        select(Employee)
        .where(and_(Employee.company_id == company_id, Employee.is_active.is_(True)))
        .order_by(Employee.name)
    )
    employees = emp_result.scalars().all()

    if not employees:
        return []

    employee_ids = [e.id for e in employees]

    # Fetch all attendance records for the month in one query
    log_result = await db.execute(
        select(AttendanceLog).where(
            and_(
                AttendanceLog.employee_id.in_(employee_ids),
                func.extract("year", AttendanceLog.date) == year,
                func.extract("month", AttendanceLog.date) == month,
            )
        )
    )
    all_logs = log_result.scalars().all()

    # Group logs by employee
    logs_by_employee: dict[uuid.UUID, list[AttendanceLog]] = {e.id: [] for e in employees}
    for log in all_logs:
        logs_by_employee[log.employee_id].append(log)

    response = []
    for emp in employees:
        emp_logs = sorted(logs_by_employee[emp.id], key=lambda l: l.date)
        days_present = sum(1 for l in emp_logs if l.status == AttendanceStatus.present)
        days_absent = sum(1 for l in emp_logs if l.status == AttendanceStatus.absent)
        total_ot = sum(l.overtime_hours or 0.0 for l in emp_logs)

        response.append(
            MonthlyAttendanceResponse(
                employee_id=emp.id,
                employee_name=emp.name,
                year=year,
                month=month,
                records=[AttendanceResponse.model_validate(l) for l in emp_logs],
                days_present=days_present,
                days_absent=days_absent,
                total_overtime_hours=round(total_ot, 2),
            )
        )

    return response
