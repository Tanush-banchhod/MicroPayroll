"""Pydantic schemas for payroll calculation endpoint."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CalculateRequest(BaseModel):
    """Request body for POST /api/payroll/calculate."""

    employee_id: str = Field(..., description="Employee identifier (any string for preview)")
    base_salary: float = Field(..., gt=0, description="Full-month basic salary in INR")
    working_days: int = Field(..., ge=0, le=31, description="Days present this month")
    overtime_hours: float = Field(0.0, ge=0, description="Total overtime hours this month")
    unpaid_leave_days: int = Field(0, ge=0, description="Days of unpaid leave")
    festival_bonus: bool = Field(False, description="Whether festival bonus applies this month")
    state: str = Field("Maharashtra", description="State code for Professional Tax lookup")
    working_days_per_month: Optional[int] = Field(None, description="Override standard 26 days")
    overtime_multiplier: Optional[float] = Field(None, description="Override 2.0× OT rate")


class CalculateResponse(BaseModel):
    """Full payroll breakdown returned by the calculate endpoint."""

    basic: float
    overtime_pay: float
    leave_deduction: float
    festival_bonus_amount: float
    gross: float
    pf_employee: float
    esic_employee: float
    professional_tax: float
    total_deductions: float
    net_pay: float
    employer_pf: float
    employer_esic: float
    cost_to_company: float
    breakdown: dict
