from __future__ import annotations

import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks

from ..config import get_settings, load_message_templates
from ..db import AsyncSessionLocal
from ..services.whatsapp import build_twiml_message, parse_twilio_payload
from ..services.conversation import ConversationManager

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


def _flatten_form(form) -> dict:
	"""Convert Starlette FormData to plain dict."""
	payload: dict = {}
	for key in form.keys():
		values = form.getlist(key)
		payload[key] = values if len(values) > 1 else form.get(key)
	return payload


async def _handle_conversation_async(payload: dict, settings):
	"""Handle conversational agent flow in background."""
	async with AsyncSessionLocal() as session:
		try:
			manager = ConversationManager(settings)
			replies = await manager.handle_payload(payload, session)
			await session.commit()
			message = parse_twilio_payload(payload)
			await manager.send_replies(message.from_number, replies)
		except Exception as e:
			import logging
			logger = logging.getLogger(__name__)
			logger.error(f"Conversation error: {str(e)}")
			await session.rollback()


@router.post("/whatsapp")
async def whatsapp_webhook(
	request: Request,
	background_tasks: BackgroundTasks,
) -> Response:
	"""
	Handle Twilio WhatsApp webhook payloads.
	
	Returns immediate TwiML acknowledgement while workflow executes in background.
	"""
	settings = get_settings()
	form = await request.form()
	payload = _flatten_form(form)
	templates = load_message_templates()
	message = parse_twilio_payload(payload)
	logger.info(
		"Webhook received: from=%s media=%s body=%s",
		message.from_number,
		len(message.media),
		(message.body or "")[:120],
	)

	# For now, send default acknowledgement
	# The workflow will send more specific responses based on content
	response_text = templates.get("acknowledgement") or "Received. Processing your submission..."
	
	# Start conversational flow in background
	logger.info("Webhook start workflow: from=%s", message.from_number)
	background_tasks.add_task(_handle_conversation_async, payload, settings)
	
	return Response(content=build_twiml_message(response_text), media_type="application/xml")
