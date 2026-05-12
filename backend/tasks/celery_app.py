from __future__ import annotations

from celery import Celery

from ..config import get_settings

_settings = get_settings()

celery_app = Celery(
    "riyaaz",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
)
celery_app.conf.task_default_queue = "riyaaz"
