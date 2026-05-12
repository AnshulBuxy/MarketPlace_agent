from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..config import get_settings
from ..services.whatsapp import send_twilio_whatsapp_message

router = APIRouter(prefix="/admin", tags=["admin"])


class WhatsAppSendRequest(BaseModel):
	"""Request body for a test WhatsApp send."""

	to_number: str = Field(..., examples=["whatsapp:+91xxxxxxxxxx"])
	body: str = Field(..., min_length=1)


@router.get("/ping")
def admin_ping() -> dict:
	"""Simple admin ping endpoint."""
	return {"status": "ok"}


@router.post("/whatsapp/send")
async def send_whatsapp_message(request: WhatsAppSendRequest) -> dict:
	"""Send a WhatsApp message through Twilio for testing."""
	settings = get_settings()
	try:
		result = await send_twilio_whatsapp_message(settings, request.to_number, request.body)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=502, detail=f"Twilio send failed: {exc}") from exc
	return {
		"status": "sent",
		"message_sid": result.message_sid,
		"to_number": result.to_number,
		"from_number": result.from_number,
	}
