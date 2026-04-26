"""Celery async tasks (stubs — filled out in Phase 4)."""

from api.worker import celery_app


@celery_app.task(name="tasks.send_daily_summary")
def send_daily_summary(company_id: str) -> None:
    """Send owner's WhatsApp daily attendance summary at shift end + 15 min."""
    # Phase 4 implementation
    pass


@celery_app.task(name="tasks.send_payslip")
def send_payslip(employee_id: str, run_id: str) -> None:
    """Send payslip PDF via WhatsApp or email."""
    # Phase 3 implementation
    pass
