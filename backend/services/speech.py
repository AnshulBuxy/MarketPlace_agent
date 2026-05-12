from __future__ import annotations

import asyncio

import httpx

from ..config import Settings


class SpeechService:
	"""Speech recognition wrapper."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	async def transcribe_audio(
		self,
		audio_bytes: bytes,
		filename: str,
		content_type: str,
	) -> str | None:
		"""Transcribe audio using Whisper API."""
		if not self._settings.openai_api_key:
			return None

		headers = {"Authorization": f"Bearer {self._settings.openai_api_key}"}
		data = {"model": self._settings.whisper_model}
		files = {"file": (filename, audio_bytes, content_type)}
		last_error: Exception | None = None

		for attempt in range(self._settings.http_max_retries):
			try:
				async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
					response = await client.post(
						"https://api.openai.com/v1/audio/transcriptions",
						headers=headers,
						data=data,
						files=files,
					)
					response.raise_for_status()
				payload = response.json()
				return payload.get("text")
			except httpx.HTTPError as exc:
				last_error = exc
				if attempt < self._settings.http_max_retries - 1:
					await asyncio.sleep(2**attempt)
					continue
				raise
		if last_error:
			raise last_error
		return None
