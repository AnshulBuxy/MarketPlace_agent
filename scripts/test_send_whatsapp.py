from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import get_settings
from backend.services.whatsapp import send_meta_whatsapp_message

TO_NUMBER = "917869291927"  # E.164, no whatsapp: prefix needed
TEST_BODY = "Hello from Banao backend — Meta Cloud API test message."


async def main() -> None:
    """Send a test WhatsApp message via Meta Cloud API."""
    settings = get_settings()
    print(f"Sending to {TO_NUMBER} via META_PHONE_NUMBER_ID={settings.meta_phone_number_id}...")
    result = await send_meta_whatsapp_message(settings, to=TO_NUMBER, text=TEST_BODY)
    print({"status": "sent", "message_id": result.message_id, "to_number": result.to_number})


if __name__ == "__main__":
    asyncio.run(main())
