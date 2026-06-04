"""Quick smoke-test for Groq chat via GeminiChatService (Groq primary, Gemini fallback)."""

import asyncio
import sys
from pathlib import Path

# Make sure the repo root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import get_settings
from backend.services.llm import GeminiChatService


async def main() -> None:
    settings = get_settings()

    print("=" * 50)
    print("Groq chat smoke-test")
    print(f"  groq_chat_model : {settings.groq_chat_model}")
    print(f"  groq_api_key    : {'set' if settings.groq_api_key else 'NOT SET'}")
    print(f"  gemini fallback : {'set' if settings.google_api_key else 'NOT SET'}")
    print("=" * 50)

    service = GeminiChatService(settings)

    prompt = (
        'Reply with ONLY valid JSON: {"status": "ok", "message": "<one fun fact about artisans>"}'
    )

    print("\nSending prompt...")
    result = await service.generate_json(prompt)

    print("\nParsed response:")
    for k, v in result.items():
        print(f"  {k}: {v}")

    print("\nTest passed ✓")


if __name__ == "__main__":
    asyncio.run(main())
