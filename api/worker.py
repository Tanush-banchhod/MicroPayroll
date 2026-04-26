"""Celery worker configuration."""

import os

from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "micropayroll",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["api.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Expose as `app` so `celery -A api.worker worker` resolves correctly
app = celery_app
