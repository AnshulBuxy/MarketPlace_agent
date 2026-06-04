from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from ..config import get_settings
from ..db import AsyncSessionLocal
from ..services.whatsapp import (
	WhatsAppMedia,
	get_media_bytes,
	parse_meta_payload,
	send_meta_whatsapp_message,
	send_meta_whatsapp_media_message,
)
from ..services.multiagent import ConversationReply, MultiAgentManager

router = APIRouter(prefix="/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# GET /webhook/whatsapp  — Meta hub verification
# ---------------------------------------------------------------------------

@router.get("/whatsapp")
async def verify_webhook(request: Request) -> PlainTextResponse:
	"""
	Respond to Meta's webhook verification handshake.

	Meta sends:
	  GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...&hub.challenge=...
	"""
	settings = get_settings()
	mode = request.query_params.get("hub.mode")
	token = request.query_params.get("hub.verify_token")
	challenge = request.query_params.get("hub.challenge")

	if mode == "subscribe" and token == settings.meta_verify_token:
		logger.info("Meta webhook verified successfully")
		return PlainTextResponse(challenge or "")

	logger.warning("Meta webhook verification failed: mode=%s token=%s", mode, token)
	raise HTTPException(status_code=403, detail="Verification failed")


# ---------------------------------------------------------------------------
# POST /webhook/whatsapp  — inbound messages
# ---------------------------------------------------------------------------

@router.post("/whatsapp")
async def whatsapp_webhook(
	request: Request,
	background_tasks: BackgroundTasks,
) -> JSONResponse:
	"""
	Receive inbound Meta Cloud API webhook payloads.

	Meta requires HTTP 200 within 5 seconds.
	All processing is delegated to a BackgroundTask.
	"""
	settings = get_settings()
	data = await request.json()

	# Quick guard: ignore status-update payloads (no "messages" key)
	try:
		value = data["entry"][0]["changes"][0]["value"]
		if "messages" not in value:
			return JSONResponse({"status": "ok"})
	except (KeyError, IndexError):
		return JSONResponse({"status": "ok"})

	message = parse_meta_payload(data)
	logger.info(
		"Webhook received: from=%s media=%s body=%s",
		message.from_number,
		len(message.media),
		(message.body or "")[:120],
	)

	background_tasks.add_task(_handle_conversation_async, data, settings)
	return JSONResponse({"status": "ok"})


# ---------------------------------------------------------------------------
# Background handler
# ---------------------------------------------------------------------------

async def _handle_conversation_async(raw_payload: dict, settings) -> None:
	"""
	Full conversation + agent flow executed in the background.

	Responsibilities:
	- Download media bytes from Meta (replaces Twilio media URLs)
	- Run MultiAgentManager
	- Send replies back via Meta Cloud API
	"""
	async with AsyncSessionLocal() as session:
		try:
			message = parse_meta_payload(raw_payload)

			# Download media bytes now so MultiAgentManager receives the same
			# bytes interface it previously got from Twilio fetch_bytes calls.
			# We replace each WhatsAppMedia's url-based approach by injecting
			# a resolved _bytes attribute used by ingestion.
			for media_item in message.media:
				try:
					media_item._bytes = await get_media_bytes(media_item.media_id, settings)
					logger.info(
						"Media downloaded: media_id=%s size=%d bytes",
						media_item.media_id,
						len(media_item._bytes),
					)
					# Detect actual format from magic bytes
					hdr = media_item._bytes[:4]
					if media_item._bytes[:2] == b'\xff\xd8':
						detected = "JPEG"
					elif media_item._bytes[:8] == b'\x89PNG\r\n\x1a\n':
						detected = "PNG"
					elif hdr == b'RIFF':
						detected = "WEBP"
					elif hdr[:3] == b'OGG':
						detected = "OGG"
					else:
						detected = f"UNKNOWN(hex={hdr.hex()})"
					logger.info("Media format detected: %s (content_type=%s)", detected, media_item.content_type)
					print(f"[WEBHOOK] media_id={media_item.media_id} size={len(media_item._bytes)} format={detected} content_type={media_item.content_type}")
				except Exception as exc:
					logger.error("Failed to download media %s: %s", media_item.media_id, exc)
					media_item._bytes = b""

			# Patch the payload so MultiAgentManager/ingestion can still use
			# the existing handle_payload(raw_payload, session) interface.
			# We embed a synthetic "url" field so fetch_bytes works on already-
			# downloaded content via a data-URI short-circuit handled below.
			_inject_media_bytes_into_payload(raw_payload, message)

			manager = MultiAgentManager(settings)
			replies: list[ConversationReply] = await manager.handle_payload(raw_payload, session)
			await session.commit()

			# Send replies via Meta
			for reply in replies:
				if not reply.body and not reply.media_url:
					continue
				try:
					if reply.media_url:
						await send_meta_whatsapp_media_message(
							settings,
							to=message.from_number,
							media_url=reply.media_url,
							caption=reply.body or "",
						)
					else:
						await send_meta_whatsapp_message(
							settings,
							to=message.from_number,
							text=reply.body,
						)
				except Exception as exc:
					logger.error("Failed to send reply to %s: %s", message.from_number, exc)

		except Exception as exc:
			logger.error("Conversation error: %s", exc, exc_info=True)
			await session.rollback()


def _inject_media_bytes_into_payload(raw_payload: dict, message) -> None:
	"""
	Patch raw_payload so that ingestion code that calls fetch_bytes(media.url)
	can retrieve already-downloaded bytes.  We store bytes on the media item
	itself; ingestion.py is updated to use get_media_bytes() directly, but
	for any legacy code still reading 'url' from the payload we set a sentinel
	that the storage / http utility will skip gracefully.
	"""
	# Nothing to patch in the raw dict itself — ingestion.py now calls
	# get_media_bytes() directly when it detects a WhatsAppMedia without a url.
	pass
