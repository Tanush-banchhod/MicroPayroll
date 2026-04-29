"""Pydantic schemas for payroll run endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from api.models.payroll import PayrollRunStatus


class PayrollRunCreate(BaseModel):
    company_id: uuid.UUID
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2020, le=2100)


class PayrollRunResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    month: int
    year: int
    status: PayrollRunStatus
    total_payout: Optional[float]
    run_at: Optional[datetime]
    created_by: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PayrollLineItemResponse(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    employee_id: uuid.UUID
    basic: float
    overtime_pay: float
    leave_deduction: float
    festival_bonus: float
    gross: float
    pf_employee: float
    esic_employee: float
    professional_tax: float
    total_deductions: float
    net_pay: float
    snapshot: Optional[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class PayrollRunDetail(PayrollRunResponse):
    """Payroll run with all employee line items."""

    line_items: list[PayrollLineItemResponse] = []
