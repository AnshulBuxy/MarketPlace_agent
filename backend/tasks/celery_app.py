from __future__ import annotations

from celery import Celery

from ..config import get_settings

_settings = get_settings()

celery_broker = _settings.celery_broker_url or "redis://localhost:6379/0"
celery_backend = _settings.celery_result_backend or "redis://localhost:6379/0"

celery_app = Celery(
    "riyaaz",
    broker=celery_broker,
    backend=celery_backend,
)
celery_app.conf.task_default_queue = "riyaaz"
