"""Pydantic schemas for company endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompanyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    gstin: Optional[str] = Field(None, max_length=15)
    state: str = Field("Maharashtra", max_length=100)
    whatsapp_number: Optional[str] = Field(None, max_length=20)
    owner_phone: Optional[str] = Field(None, max_length=20)


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    address: Optional[str]
    gstin: Optional[str]
    state: str
    whatsapp_number: Optional[str]
    owner_phone: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
