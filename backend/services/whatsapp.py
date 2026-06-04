from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import Settings


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class WhatsAppMedia:
	"""A media item referenced by a Meta Cloud API message."""

	media_id: str
	content_type: str  # e.g. "image/jpeg", "audio/ogg"

	def is_image(self) -> bool:
		return self.content_type.startswith("image/")

	def is_audio(self) -> bool:
		return self.content_type.startswith("audio/")


@dataclass
class WhatsAppInboundMessage:
	"""Normalised Meta Cloud API inbound payload."""

	from_number: str
	body: str
	message_id: str | None
	media: list[WhatsAppMedia]
	raw_payload: dict[str, Any]


@dataclass
class WhatsAppSendResult:
	"""Meta Cloud API outbound send response summary."""

	message_id: str
	to_number: str


# ---------------------------------------------------------------------------
# Backward-compat aliases (used by ingestion.py & tasks/orchestrator.py)
# ---------------------------------------------------------------------------
TwilioMedia = WhatsAppMedia
TwilioInboundMessage = WhatsAppInboundMessage
TwilioSendResult = WhatsAppSendResult


# ---------------------------------------------------------------------------
# Inbound parsing
# ---------------------------------------------------------------------------

def parse_meta_payload(data: dict[str, Any]) -> WhatsAppInboundMessage:
	"""Parse a Meta Cloud API webhook JSON body into a structured message."""
	try:
		value = data["entry"][0]["changes"][0]["value"]
	except (KeyError, IndexError) as exc:
		raise ValueError(f"Unexpected Meta payload structure: {exc}") from exc

	messages = value.get("messages", [])
	if not messages:
		# Status update or other event — return empty message
		return WhatsAppInboundMessage(
			from_number="",
			body="",
			message_id=None,
			media=[],
			raw_payload=data,
		)

	msg = messages[0]
	from_number = _normalize_whatsapp_number(msg.get("from", ""))
	message_id = msg.get("id")
	msg_type = msg.get("type", "text")

	body = ""
	media: list[WhatsAppMedia] = []

	if msg_type == "text":
		body = msg.get("text", {}).get("body", "")

	elif msg_type == "image":
		media_id = msg["image"]["id"]
		mime = msg["image"].get("mime_type", "image/jpeg")
		media.append(WhatsAppMedia(media_id=media_id, content_type=mime))

	elif msg_type == "audio":
		media_id = msg["audio"]["id"]
		mime = msg["audio"].get("mime_type", "audio/ogg")
		media.append(WhatsAppMedia(media_id=media_id, content_type=mime))

	elif msg_type == "document":
		media_id = msg["document"]["id"]
		mime = msg["document"].get("mime_type", "application/octet-stream")
		media.append(WhatsAppMedia(media_id=media_id, content_type=mime))

	# Capture any text caption attached to a media message
	if msg_type in {"image", "audio", "document"}:
		body = msg.get(msg_type, {}).get("caption", "")

	return WhatsAppInboundMessage(
		from_number=from_number,
		body=body,
		message_id=message_id,
		media=media,
		raw_payload=data,
	)


# Keep old name as alias so existing code that calls parse_twilio_payload still works
def parse_twilio_payload(data: dict[str, Any]) -> WhatsAppInboundMessage:
	"""Alias for parse_meta_payload — kept for backward compatibility."""
	return parse_meta_payload(data)


# ---------------------------------------------------------------------------
# Media download
# ---------------------------------------------------------------------------

async def get_media_bytes(media_id: str, settings: Settings) -> bytes:
	"""Download media bytes from Meta Cloud API using a media_id."""
	if not settings.meta_access_token:
		raise ValueError("META_ACCESS_TOKEN is not configured")

	headers = {"Authorization": f"Bearer {settings.meta_access_token}"}
	async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
		# Step 1 — resolve media URL
		r = await client.get(
			f"https://graph.facebook.com/v19.0/{media_id}",
			headers=headers,
		)
		r.raise_for_status()
		media_url = r.json()["url"]

		# Step 2 — download bytes
		r2 = await client.get(media_url, headers=headers)
		r2.raise_for_status()
		return r2.content


# ---------------------------------------------------------------------------
# Outbound messaging
# ---------------------------------------------------------------------------

def _normalize_whatsapp_number(number: str) -> str:
	"""Strip any whatsapp: prefix and return a plain E.164 number."""
	if number.startswith("whatsapp:"):
		return number[len("whatsapp:"):]
	return number


async def send_meta_whatsapp_message(
	settings: Settings,
	to: str,
	text: str,
) -> WhatsAppSendResult:
	"""Send a plain-text WhatsApp message via Meta Cloud API."""
	if not settings.meta_access_token or not settings.meta_phone_number_id:
		raise ValueError("META_ACCESS_TOKEN and META_PHONE_NUMBER_ID must be configured")

	to = _normalize_whatsapp_number(to)
	url = f"https://graph.facebook.com/v19.0/{settings.meta_phone_number_id}/messages"
	headers = {
		"Authorization": f"Bearer {settings.meta_access_token}",
		"Content-Type": "application/json",
	}
	body = {
		"messaging_product": "whatsapp",
		"to": to,
		"type": "text",
		"text": {"body": text},
	}

	async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
		response = await client.post(url, headers=headers, json=body)
		if response.status_code >= 400:
			raise httpx.HTTPStatusError(
				f"Meta send failed: {response.status_code} {response.text}",
				request=response.request,
				response=response,
			)

	result = response.json()
	message_id = result.get("messages", [{}])[0].get("id", "")
	return WhatsAppSendResult(message_id=message_id, to_number=to)


async def send_meta_whatsapp_media_message(
	settings: Settings,
	to: str,
	media_url: str,
	caption: str = "",
) -> WhatsAppSendResult:
	"""Send an image message with optional caption via Meta Cloud API."""
	if not settings.meta_access_token or not settings.meta_phone_number_id:
		raise ValueError("META_ACCESS_TOKEN and META_PHONE_NUMBER_ID must be configured")

	to = _normalize_whatsapp_number(to)
	url = f"https://graph.facebook.com/v19.0/{settings.meta_phone_number_id}/messages"
	headers = {
		"Authorization": f"Bearer {settings.meta_access_token}",
		"Content-Type": "application/json",
	}
	body = {
		"messaging_product": "whatsapp",
		"to": to,
		"type": "image",
		"image": {"link": media_url, "caption": caption},
	}

	async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
		response = await client.post(url, headers=headers, json=body)
		if response.status_code >= 400:
			raise httpx.HTTPStatusError(
				f"Meta media send failed: {response.status_code} {response.text}",
				request=response.request,
				response=response,
			)

	result = response.json()
	message_id = result.get("messages", [{}])[0].get("id", "")
	return WhatsAppSendResult(message_id=message_id, to_number=to)


# ---------------------------------------------------------------------------
# Backward-compat wrappers for code that still calls the old Twilio functions
# ---------------------------------------------------------------------------

async def send_twilio_whatsapp_message(
	settings: Settings,
	to_number: str,
	body: str,
	from_number: str | None = None,  # ignored — Meta uses phone_number_id
) -> WhatsAppSendResult:
	"""Backward-compat alias → send_meta_whatsapp_message."""
	return await send_meta_whatsapp_message(settings, to=to_number, text=body)


async def send_twilio_whatsapp_media_message(
	settings: Settings,
	to_number: str,
	body: str,
	media_url: str,
	from_number: str | None = None,  # ignored — Meta uses phone_number_id
) -> WhatsAppSendResult:
	"""Backward-compat alias → send_meta_whatsapp_media_message."""
	return await send_meta_whatsapp_media_message(
		settings, to=to_number, media_url=media_url, caption=body
	)
