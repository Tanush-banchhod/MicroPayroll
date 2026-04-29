"""Pydantic schemas for employee endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    base_salary: float = Field(..., gt=0, description="Monthly base salary in INR")
    phone_number: Optional[str] = Field(None, max_length=20)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_ifsc: Optional[str] = Field(None, max_length=11)
    pf_account: Optional[str] = Field(None, max_length=50)
    joined_at: Optional[datetime] = None


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[str] = Field(None, max_length=100)
    base_salary: Optional[float] = Field(None, gt=0)
    phone_number: Optional[str] = Field(None, max_length=20)
    bank_account: Optional[str] = Field(None, max_length=50)
    bank_ifsc: Optional[str] = Field(None, max_length=11)
    pf_account: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class EmployeeResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    role: Optional[str]
    base_salary: float
    phone_number: Optional[str]
    bank_account: Optional[str]
    bank_ifsc: Optional[str]
    pf_account: Optional[str]
    is_active: bool
    joined_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}
