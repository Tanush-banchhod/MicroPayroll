"""Payroll run and payroll line item models."""

import uuid
from datetime import datetime

from sqlalchemy import Integer, Float, DateTime, ForeignKey, func, String
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
import enum

from api.models.base import Base


class PayrollRunStatus(str, enum.Enum):
    draft = "draft"
    approved = "approved"
    paid = "paid"


class PayrollRun(Base):
    __tablename__ = "payroll_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    month: Mapped[int] = mapped_column(Integer, nullable=False)   # 1–12
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PayrollRunStatus] = mapped_column(
        SAEnum(PayrollRunStatus, name="payroll_run_status"),
        nullable=False,
        default=PayrollRunStatus.draft,
    )
    total_payout: Mapped[float | None] = mapped_column(Float)
    run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="payroll_runs")  # type: ignore[name-defined]
    line_items: Mapped[list["PayrollLineItem"]] = relationship(back_populates="run")


class PayrollLineItem(Base):
    """One row per employee per payroll run — stores the full breakdown snapshot."""

    __tablename__ = "payroll_line_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payroll_runs.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )

    # Earnings
    basic: Mapped[float] = mapped_column(Float, nullable=False)
    overtime_pay: Mapped[float] = mapped_column(Float, default=0.0)
    leave_deduction: Mapped[float] = mapped_column(Float, default=0.0)
    festival_bonus: Mapped[float] = mapped_column(Float, default=0.0)
    gross: Mapped[float] = mapped_column(Float, nullable=False)

    # Deductions
    pf_employee: Mapped[float] = mapped_column(Float, default=0.0)
    esic_employee: Mapped[float] = mapped_column(Float, default=0.0)
    professional_tax: Mapped[float] = mapped_column(Float, default=0.0)
    total_deductions: Mapped[float] = mapped_column(Float, nullable=False)
    net_pay: Mapped[float] = mapped_column(Float, nullable=False)

    # Full audit trail — preserves calculation details even if rules change later
    snapshot: Mapped[dict | None] = mapped_column(JSONB)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    run: Mapped[PayrollRun] = relationship(back_populates="line_items")
    employee: Mapped["Employee"] = relationship(back_populates="payroll_line_items")  # type: ignore[name-defined]
