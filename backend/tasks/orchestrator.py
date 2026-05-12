from __future__ import annotations

import asyncio

from ..agents.ingestion import ingest_twilio_message
from ..config import get_settings
from ..db import AsyncSessionLocal
from ..services.whatsapp import parse_twilio_payload
from .celery_app import celery_app


@celery_app.task(name="tasks.ingest_twilio_payload")
def ingest_twilio_payload_task(payload: dict) -> str | None:
	"""Celery task to ingest a Twilio payload."""
	return asyncio.run(_ingest(payload))


async def _ingest(payload: dict) -> str | None:
	"""Async ingestion workflow for Celery task."""
	settings = get_settings()
	message = parse_twilio_payload(payload)
	async with AsyncSessionLocal() as session:
		result = await ingest_twilio_message(message, session, settings)
		await session.commit()
		return str(result.product_id) if result.product_id else None
