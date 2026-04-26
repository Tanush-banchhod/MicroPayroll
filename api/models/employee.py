"""Employee model."""

import uuid
from datetime import datetime

from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.base import Base


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str | None] = mapped_column(String(100))
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    phone_number: Mapped[str | None] = mapped_column(String(20))
    bank_account: Mapped[str | None] = mapped_column(String(50))
    bank_ifsc: Mapped[str | None] = mapped_column(String(11))
    pf_account: Mapped[str | None] = mapped_column(String(50))
    # 128-dimensional face encoding (dlib) — stored as float array, NOT a photo
    face_encoding: Mapped[list[float] | None] = mapped_column(ARRAY(Float))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    company: Mapped["Company"] = relationship(back_populates="employees")  # type: ignore[name-defined]
    attendance_logs: Mapped[list["AttendanceLog"]] = relationship(back_populates="employee")  # type: ignore[name-defined]
    payroll_line_items: Mapped[list["PayrollLineItem"]] = relationship(back_populates="employee")  # type: ignore[name-defined]
