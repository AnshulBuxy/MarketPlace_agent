from __future__ import annotations

import asyncio
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import get_settings
from backend.services.whatsapp import send_twilio_whatsapp_message


TO_NUMBER = "whatsapp:+917869291927"
TEST_BODY = "Hello from Riyaaz backend test message."
FROM_NUMBER = "whatsapp:+14155238886"


async def main() -> None:
    """Send a temporary WhatsApp test message."""
    settings = get_settings()
    result = await send_twilio_whatsapp_message(settings, TO_NUMBER, TEST_BODY, from_number=FROM_NUMBER)
    print({"status": "sent", "message_sid": result.message_sid, "to_number": result.to_number, "from_number": result.from_number})


if __name__ == "__main__":
    asyncio.run(main())
