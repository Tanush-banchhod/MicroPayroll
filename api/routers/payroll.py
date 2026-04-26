"""Payroll router — preview calculation + run management."""

from fastapi import APIRouter, HTTPException, status

from engine.salary import EmployeeInput, calculate
from engine.compliance.india import load_rules
from api.schemas.payroll import CalculateRequest, CalculateResponse

router = APIRouter(prefix="/api/payroll", tags=["payroll"])


@router.post(
    "/calculate",
    response_model=CalculateResponse,
    summary="Preview salary calculation",
    description=(
        "Accepts employee attendance inputs and returns a full salary breakdown. "
        "This is a pure calculation — no database writes occur."
    ),
)
def calculate_payroll(req: CalculateRequest) -> CalculateResponse:
    try:
        rules = load_rules(req.state)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    inp = EmployeeInput(
        employee_id=req.employee_id,
        base_salary=req.base_salary,
        working_days=req.working_days,
        overtime_hours=req.overtime_hours,
        unpaid_leave_days=req.unpaid_leave_days,
        festival_bonus=req.festival_bonus,
        state=req.state,
        working_days_per_month=req.working_days_per_month,
        overtime_multiplier=req.overtime_multiplier,
    )

    result = calculate(inp, rules)

    return CalculateResponse(
        basic=result.basic,
        overtime_pay=result.overtime_pay,
        leave_deduction=result.leave_deduction,
        festival_bonus_amount=result.festival_bonus_amount,
        gross=result.gross,
        pf_employee=result.pf_employee,
        esic_employee=result.esic_employee,
        professional_tax=result.professional_tax,
        total_deductions=result.total_deductions,
        net_pay=result.net_pay,
        employer_pf=result.employer_pf,
        employer_esic=result.employer_esic,
        cost_to_company=result.cost_to_company,
        breakdown=result.breakdown,
    )
