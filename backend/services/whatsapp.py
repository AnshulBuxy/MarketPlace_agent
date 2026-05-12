from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from xml.etree.ElementTree import Element, SubElement, tostring

import httpx

from ..config import Settings


@dataclass
class TwilioMedia:
	"""Twilio media item."""

	url: str
	content_type: str

	def is_image(self) -> bool:
		"""Return True if media is an image."""
		return self.content_type.startswith("image/")

	def is_audio(self) -> bool:
		"""Return True if media is audio."""
		return self.content_type.startswith("audio/")


@dataclass
class TwilioInboundMessage:
	"""Normalized Twilio inbound payload."""

	from_number: str
	body: str
	message_sid: str | None
	media: list[TwilioMedia]
	raw_payload: dict[str, Any]


@dataclass
class TwilioSendResult:
	"""Twilio outbound send response summary."""

	message_sid: str
	to_number: str
	from_number: str


def parse_twilio_payload(payload: dict[str, Any]) -> TwilioInboundMessage:
	"""Parse Twilio form payload into a structured message."""
	def _first(value: Any) -> Any:
		if isinstance(value, list):
			return value[0] if value else ""
		return value

	from_number = str(_first(payload.get("From", "")))
	body = str(_first(payload.get("Body", "")))
	message_sid = _first(payload.get("MessageSid"))
	num_media = int(_first(payload.get("NumMedia", 0)) or 0)
	media: list[TwilioMedia] = []
	for index in range(num_media):
		url_key = f"MediaUrl{index}"
		type_key = f"MediaContentType{index}"
		url = _first(payload.get(url_key))
		content_type = _first(payload.get(type_key))
		if url and content_type:
			media.append(TwilioMedia(url=str(url), content_type=str(content_type)))
	return TwilioInboundMessage(
		from_number=from_number,
		body=body,
		message_sid=message_sid,
		media=media,
		raw_payload=payload,
	)


def build_twiml_message(body: str) -> str:
	"""Build a TwiML response message."""
	response = Element("Response")
	message = SubElement(response, "Message")
	message.text = body
	return tostring(response, encoding="utf-8", xml_declaration=False).decode("utf-8")


def _normalize_whatsapp_number(number: str) -> str:
	"""Ensure a Twilio WhatsApp number uses the whatsapp: prefix."""
	if number.startswith("whatsapp:"):
		return number
	return f"whatsapp:{number}"


async def send_twilio_whatsapp_message(
	settings: Settings,
	to_number: str,
	body: str,
	from_number: str | None = None,
) -> TwilioSendResult:
	"""Send a WhatsApp message through Twilio."""
	if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_whatsapp_number:
		raise ValueError("Twilio credentials are not configured")

	from_whatsapp_number = from_number or settings.twilio_whatsapp_number
	url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
	payload = {
		"From": _normalize_whatsapp_number(from_whatsapp_number),
		"To": _normalize_whatsapp_number(to_number),
		"Body": body,
	}
	async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
		response = await client.post(url, data=payload, auth=(settings.twilio_account_sid, settings.twilio_auth_token))
		if response.status_code >= 400:
			raise httpx.HTTPStatusError(
				f"Twilio send failed: {response.status_code} {response.text}",
				request=response.request,
				response=response,
			)
	result = response.json()
	return TwilioSendResult(
		message_sid=str(result.get("sid", "")),
		to_number=str(result.get("to", to_number)),
		from_number=str(result.get("from", from_whatsapp_number)),
	)


async def send_twilio_whatsapp_media_message(
	settings: Settings,
	to_number: str,
	body: str,
	media_url: str,
	from_number: str | None = None,
) -> TwilioSendResult:
	"""Send a WhatsApp message with media through Twilio."""
	if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_whatsapp_number:
		raise ValueError("Twilio credentials are not configured")

	from_whatsapp_number = from_number or settings.twilio_whatsapp_number
	url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.twilio_account_sid}/Messages.json"
	payload = {
		"From": _normalize_whatsapp_number(from_whatsapp_number),
		"To": _normalize_whatsapp_number(to_number),
		"Body": body,
		"MediaUrl": media_url,
	}
	async with httpx.AsyncClient(timeout=settings.http_timeout_seconds) as client:
		response = await client.post(url, data=payload, auth=(settings.twilio_account_sid, settings.twilio_auth_token))
		if response.status_code >= 400:
			raise httpx.HTTPStatusError(
				f"Twilio send failed: {response.status_code} {response.text}",
				request=response.request,
				response=response,
			)
	result = response.json()
	return TwilioSendResult(
		message_sid=str(result.get("sid", "")),
		to_number=str(result.get("to", to_number)),
		from_number=str(result.get("from", from_whatsapp_number)),
	)
