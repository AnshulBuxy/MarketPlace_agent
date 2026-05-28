from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
	sys.path.insert(0, str(ROOT))

from backend.config import get_settings
from backend.services.speech import SpeechService
from backend.utils.http import fetch_bytes


async def _run() -> int:
	parser = argparse.ArgumentParser(description="Check WhatsApp audio transcription using the backend Whisper integration.")
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument("--file", type=Path, help="Local audio file to transcribe")
	group.add_argument("--url", help="Remote audio URL to transcribe")
	parser.add_argument("--provider", choices=["auto", "groq", "openai"], default="auto", help="Force a transcription provider to test")
	parser.add_argument("--filename", help="Filename sent to the transcription API")
	parser.add_argument("--content-type", default="audio/mpeg", help="Audio MIME type (default: audio/mpeg)")
	parser.add_argument("--print-bytes", action="store_true", help="Print the audio byte size before transcribing")
	args = parser.parse_args()

	settings = get_settings()
	speech = SpeechService(settings)
	provider = _resolve_provider(settings, args.provider)
	if provider is None:
		print("transcription=None")
		print("reason=no transcription provider is configured")
		return 2
	print(f"provider={provider}")
	print(f"groq_api_key={'set' if settings.groq_api_key else 'missing'}")
	print(f"groq_whisper_model={settings.groq_whisper_model}")

	if args.file:
		audio_path = args.file
		if not audio_path.exists():
			raise FileNotFoundError(f"Audio file not found: {audio_path}")
		audio_bytes = audio_path.read_bytes()
		filename = args.filename or audio_path.name
		content_type = args.content_type or "audio/mpeg"
	else:
		audio_bytes = await fetch_bytes(
			args.url,
			auth=(settings.twilio_account_sid, settings.twilio_auth_token) if settings.twilio_account_sid and settings.twilio_auth_token else None,
			timeout_seconds=settings.http_timeout_seconds,
			max_retries=settings.http_max_retries,
		)
		filename = args.filename or "audio.mp3"
		content_type = args.content_type or "audio/mpeg"

	if args.print_bytes:
		print(f"bytes={len(audio_bytes)}")
		print(f"filename={filename}")
		print(f"content_type={content_type}")

	text = await speech.transcribe_audio(audio_bytes, filename=filename, content_type=content_type)
	if text is None:
		print("transcription=None")
		print("reason=transcription returned nothing")
		return 2

	print("transcription:")
	print(text)
	return 0


def main() -> None:
	raise SystemExit(asyncio.run(_run()))


def _resolve_provider(settings, requested: str) -> str | None:
	if requested == "groq":
		return "groq" if settings.groq_api_key else None
	if requested == "openai":
		return "openai" if settings.openai_api_key else None
	if settings.groq_api_key:
		return "groq"
	if settings.openai_api_key:
		return "openai"
	return None


if __name__ == "__main__":
	main()
