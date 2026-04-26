"""Company model — top-level tenant."""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    gstin: Mapped[str | None] = mapped_column(String(15))
    state: Mapped[str] = mapped_column(String(100), nullable=False, default="Maharashtra")
    whatsapp_number: Mapped[str | None] = mapped_column(String(20))
    owner_phone: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    employees: Mapped[list["Employee"]] = relationship(back_populates="company")  # type: ignore[name-defined]
    payroll_runs: Mapped[list["PayrollRun"]] = relationship(back_populates="company")  # type: ignore[name-defined]
    compliance_rules: Mapped[list["ComplianceRule"]] = relationship(back_populates="company")  # type: ignore[name-defined]
