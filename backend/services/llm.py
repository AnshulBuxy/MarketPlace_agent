from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Any

import google.generativeai as genai
from groq import Groq

from ..config import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared JSON parsing helpers (used by both services)
# ---------------------------------------------------------------------------

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
    raise ValueError("Model response was not valid JSON")


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
    }


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


# ---------------------------------------------------------------------------
# GeminiService  (vision / multimodal extraction)
# ---------------------------------------------------------------------------

class GeminiService:
    """Multimodal extraction service — Groq vision primary, Gemini fallback."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        # Groq client (primary)
        self._groq_client: Groq | None = None
        self._groq_vision_model = settings.groq_vision_model
        if settings.groq_api_key:
            self._groq_client = Groq(api_key=settings.groq_api_key)

        # Gemini (fallback)
        self._gemini_model_name = settings.google_gemini_flash_model or "gemini-1.5-flash"
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

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

        # Gemini handles vision extraction — Groq's llama-4-scout returns empty JSON
        # for structured extraction from JPEG base64, so we use Gemini directly here.
        # Groq is still used for text-only chat (GeminiChatService).
        if not self._settings.google_api_key:
            raise RuntimeError("Neither Groq nor Google API key is configured")

        text = await asyncio.to_thread(
            self._gemini_vision_call, prompt, image_bytes, mime_type
        )
        print(f"[LLM] Gemini raw response (first 300 chars): {text[:300]}")
        payload = _parse_json(text)
        attributes = _normalize_attributes(payload)
        attributes["info_source"] = "gemini_multimodal"
        confidence = _normalize_confidence(payload.get("confidence"))
        print(f"[LLM] extract_attributes → GEMINI ({self._gemini_model_name})")
        print(f"[LLM] Extracted: name={attributes.get('name')!r} category={attributes.get('category')!r}")
        return attributes, confidence

    # ------------------------------------------------------------------
    # Internal sync helpers (run in thread)
    # ------------------------------------------------------------------

    def _groq_vision_call(
        self, prompt: str, image_bytes: bytes, mime_type: str
    ) -> str:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = self._groq_client.chat.completions.create(
            model=self._groq_vision_model,
            timeout=60,  # vision calls can be slow for large images
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64}"
                            },
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content or ""

    def _gemini_vision_call(
        self, prompt: str, image_bytes: bytes, mime_type: str
    ) -> str:
        model = genai.GenerativeModel(self._gemini_model_name)
        response = model.generate_content([
            prompt,
            {"mime_type": mime_type, "data": image_bytes},
        ])
        return response.text or ""

    # Keep for backward compat
    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        return _parse_json(text)


# ---------------------------------------------------------------------------
# GeminiChatService  (text-only chat / agent decisions)
# ---------------------------------------------------------------------------

class GeminiChatService:
    """Text-only chat service — Groq primary, Gemini fallback."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

        # Groq client (primary)
        self._groq_client: Groq | None = None
        self._groq_chat_model = settings.groq_chat_model
        if settings.groq_api_key:
            self._groq_client = Groq(api_key=settings.groq_api_key)

        # Gemini (fallback)
        self._gemini_model_name = settings.google_gemini_flash_model or "gemini-1.5-flash"
        if settings.google_api_key:
            genai.configure(api_key=settings.google_api_key)

    async def generate_json(self, prompt: str) -> dict[str, Any]:
        # Try Groq first
        if self._groq_client:
            try:
                text = await asyncio.to_thread(self._groq_chat_call, prompt)
                result = _parse_json(text)
                print(f"[LLM] generate_json → GROQ ({self._groq_chat_model})")
                return result
            except Exception as exc:
                logger.warning(
                    "[LLM] Groq chat failed, falling back to Gemini: %s", exc
                )
                print(f"[LLM] generate_json → Groq failed ({exc}), falling back to GEMINI")

        # Gemini fallback
        if not self._settings.google_api_key:
            raise RuntimeError("Neither Groq nor Google API key is configured")

        text = await asyncio.to_thread(self._gemini_chat_call, prompt)
        result = _parse_json(text)
        print(f"[LLM] generate_json → GEMINI ({self._gemini_model_name})")
        return result

    # ------------------------------------------------------------------
    # Internal sync helpers
    # ------------------------------------------------------------------

    def _groq_chat_call(self, prompt: str) -> str:
        response = self._groq_client.chat.completions.create(
            model=self._groq_chat_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content or ""

    def _gemini_chat_call(self, prompt: str) -> str:
        model = genai.GenerativeModel(self._gemini_model_name)
        response = model.generate_content(prompt)
        return response.text or ""
