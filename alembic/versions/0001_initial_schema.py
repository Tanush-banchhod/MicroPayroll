"""Initial schema — all core tables

Revision ID: 0001
Revises:
Create Date: 2024-11-01 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── companies ──────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.String(500)),
        sa.Column("gstin", sa.String(15)),
        sa.Column("state", sa.String(100), nullable=False, server_default="Maharashtra"),
        sa.Column("whatsapp_number", sa.String(20)),
        sa.Column("owner_phone", sa.String(20)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── employees ──────────────────────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100)),
        sa.Column("base_salary", sa.Float, nullable=False),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("bank_account", sa.String(50)),
        sa.Column("bank_ifsc", sa.String(11)),
        sa.Column("pf_account", sa.String(50)),
        sa.Column("face_encoding", postgresql.ARRAY(sa.Float)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("joined_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── attendance_logs ────────────────────────────────────────────────────────
    attendance_status = postgresql.ENUM(
        "present", "absent", "half_day", "holiday", name="attendance_status"
    )
    attendance_source = postgresql.ENUM(
        "whatsapp", "qr_code", "manual", name="attendance_source"
    )
    attendance_status.create(op.get_bind())
    attendance_source.create(op.get_bind())

    op.create_table(
        "attendance_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("punch_in", sa.DateTime(timezone=True)),
        sa.Column("punch_out", sa.DateTime(timezone=True)),
        sa.Column("hours_worked", sa.Float),
        sa.Column("overtime_hours", sa.Float, server_default="0"),
        sa.Column("status", sa.Enum("present", "absent", "half_day", "holiday", name="attendance_status"), nullable=False),
        sa.Column("source", sa.Enum("whatsapp", "qr_code", "manual", name="attendance_source"), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_attendance_employee_date", "attendance_logs", ["employee_id", "date"])

    # ── payroll_runs ───────────────────────────────────────────────────────────
    payroll_run_status = postgresql.ENUM(
        "draft", "approved", "paid", name="payroll_run_status"
    )
    payroll_run_status.create(op.get_bind())

    op.create_table(
        "payroll_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("month", sa.Integer, nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("status", sa.Enum("draft", "approved", "paid", name="payroll_run_status"), nullable=False, server_default="draft"),
        sa.Column("total_payout", sa.Float),
        sa.Column("run_at", sa.DateTime(timezone=True)),
        sa.Column("created_by", sa.String(255)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── payroll_line_items ─────────────────────────────────────────────────────
    op.create_table(
        "payroll_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("payroll_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("basic", sa.Float, nullable=False),
        sa.Column("overtime_pay", sa.Float, server_default="0"),
        sa.Column("leave_deduction", sa.Float, server_default="0"),
        sa.Column("festival_bonus", sa.Float, server_default="0"),
        sa.Column("gross", sa.Float, nullable=False),
        sa.Column("pf_employee", sa.Float, server_default="0"),
        sa.Column("esic_employee", sa.Float, server_default="0"),
        sa.Column("professional_tax", sa.Float, server_default="0"),
        sa.Column("total_deductions", sa.Float, nullable=False),
        sa.Column("net_pay", sa.Float, nullable=False),
        sa.Column("snapshot", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── compliance_rules ───────────────────────────────────────────────────────
    op.create_table(
        "compliance_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "company_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("config", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("compliance_rules")
    op.drop_table("payroll_line_items")
    op.drop_table("payroll_runs")
    op.drop_index("ix_attendance_employee_date", "attendance_logs")
    op.drop_table("attendance_logs")
    op.drop_table("employees")
    op.drop_table("companies")

    for name in ("payroll_run_status", "attendance_source", "attendance_status"):
        postgresql.ENUM(name=name).drop(op.get_bind())
