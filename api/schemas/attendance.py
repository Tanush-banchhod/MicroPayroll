"""Pydantic schemas for attendance endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from api.models.attendance import AttendanceStatus, AttendanceSource


class AttendanceManualCreate(BaseModel):
    employee_id: uuid.UUID
    date: date
    status: AttendanceStatus = AttendanceStatus.present
    punch_in: Optional[datetime] = None
    punch_out: Optional[datetime] = None
    overtime_hours: float = Field(0.0, ge=0)


class AttendanceResponse(BaseModel):
    id: uuid.UUID
    employee_id: uuid.UUID
    date: date
    punch_in: Optional[datetime]
    punch_out: Optional[datetime]
    hours_worked: Optional[float]
    overtime_hours: Optional[float]
    status: AttendanceStatus
    source: AttendanceSource
    created_at: datetime

    model_config = {"from_attributes": True}


class MonthlyAttendanceResponse(BaseModel):
    """Attendance grid for one employee for a full month."""

    employee_id: uuid.UUID
    employee_name: str
    year: int
    month: int
    records: list[AttendanceResponse]
    days_present: int
    days_absent: int
    total_overtime_hours: float
