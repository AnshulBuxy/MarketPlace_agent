from __future__ import annotations

import asyncio
import json
from typing import Any

import google.generativeai as genai

from ..config import Settings


class GeminiService:
	"""Gemini multimodal extraction service."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._model_name = settings.google_gemini_flash_model or "gemini-1.5-flash"
		if not settings.google_api_key:
			raise ValueError("GOOGLE_API_KEY is not configured")
		genai.configure(api_key=settings.google_api_key)

	async def extract_attributes(
		self,
		image_bytes: bytes,
		mime_type: str,
		user_description: str,
		transcription: str,
	) -> tuple[dict[str, Any], dict[str, float]]:
		"""Extract product attributes and confidence scores from an image + text."""
		prompt = (
			"You are a product attribute extractor. Return ONLY valid JSON with the following fields: "
			"name (string), category (string), materials (array of strings), "
			"dimensions (object with length,width,height,unit or note), "
			"description (string), tags (array of strings), "
			"confidence (object with name,category,materials,dimensions,description values between 0 and 1). "
			"Use the provided artisan description and transcription as hints. "
			"Do not include any extra text outside JSON.\n\n"
			f"Artisan description: {user_description or 'N/A'}\n"
			f"Audio transcription: {transcription or 'N/A'}"
		)

		def _call() -> str:
			model = genai.GenerativeModel(self._model_name)
			response = model.generate_content([
				prompt,
				{"mime_type": mime_type, "data": image_bytes},
			])
			return response.text or ""

		text = await asyncio.to_thread(_call)
		payload = self._parse_json(text)
		attributes = self._normalize_attributes(payload)
		confidence = self._normalize_confidence(payload.get("confidence"))
		return attributes, confidence

	@staticmethod
	def _parse_json(text: str) -> dict[str, Any]:
		"""Parse JSON from model output with fallback for fenced blocks."""
		clean = text.strip()
		if clean.startswith("```"):
			clean = clean.strip("`")
			clean = clean.replace("json", "", 1).strip()
		try:
			return json.loads(clean)
		except Exception:
			start = clean.find("{")
			end = clean.rfind("}")
			if start != -1 and end != -1 and end > start:
				return json.loads(clean[start : end + 1])
		raise ValueError("Gemini response was not valid JSON")

	@staticmethod
	def _normalize_attributes(payload: dict[str, Any]) -> dict[str, Any]:
		materials = payload.get("materials") or []
		if not isinstance(materials, list):
			materials = [str(materials)]
		tags = payload.get("tags") or []
		if not isinstance(tags, list):
			tags = [str(tags)]
		dimensions = payload.get("dimensions") or {}
		if not isinstance(dimensions, dict):
			dimensions = {"raw": str(dimensions)}
		return {
			"name": payload.get("name") or "",
			"category": payload.get("category") or "",
			"materials": materials,
			"dimensions": dimensions,
			"description": payload.get("description") or "",
			"tags": tags,
			"info_source": "gemini_multimodal",
		}

	@staticmethod
	def _normalize_confidence(conf: Any) -> dict[str, float]:
		def _safe_float(value: Any, default: float) -> float:
			try:
				return float(value)
			except Exception:
				return default
		if not isinstance(conf, dict):
			conf = {}
		return {
			"name": _safe_float(conf.get("name", 0.7), 0.7),
			"category": _safe_float(conf.get("category", 0.7), 0.7),
			"materials": _safe_float(conf.get("materials", 0.6), 0.6),
			"dimensions": _safe_float(conf.get("dimensions", 0.6), 0.6),
			"description": _safe_float(conf.get("description", 0.7), 0.7),
		}
