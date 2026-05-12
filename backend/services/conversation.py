from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models.conversation_session import ConversationSession
from ..models.product import Product
from ..services.llm import GeminiService
from ..services.storage import StorageService
from ..services.whatsapp import (
	parse_twilio_payload,
	send_twilio_whatsapp_media_message,
	send_twilio_whatsapp_message,
)
from ..utils.audit import log_event

logger = logging.getLogger(__name__)


@dataclass
class ConversationReply:
	body: str
	media_url: str | None = None


class ConversationManager:
	"""Conversational agent for product intake."""

	def __init__(self, settings: Settings):
		self.settings = settings

	async def handle_payload(self, payload: dict, session: AsyncSession) -> list[ConversationReply]:
		message = parse_twilio_payload(payload)
		session_state = await self._get_or_create_session(session, message.from_number)
		language = self._detect_language(message.body)
		if language:
			session_state.language = language

		replies: list[ConversationReply] = []

		if message.media:
			replies = await self._handle_media(message, session_state, session)
		else:
			replies = await self._handle_text(message.body or "", session_state, session)

		await session.flush()
		return replies

	async def send_replies(self, to_number: str, replies: list[ConversationReply]) -> None:
		for reply in replies:
			if reply.media_url:
				await send_twilio_whatsapp_media_message(
					self.settings,
					to_number=to_number,
					body=reply.body,
					media_url=reply.media_url,
				)
			else:
				await send_twilio_whatsapp_message(
					self.settings,
					to_number=to_number,
					body=reply.body,
				)

	async def _get_or_create_session(self, session: AsyncSession, phone: str) -> ConversationSession:
		state = await session.get(ConversationSession, phone)
		if state:
			return state
		state = ConversationSession(phone_number=phone, state_json={})
		session.add(state)
		await session.flush()
		return state

	def _detect_language(self, text: str | None) -> str | None:
		if not text:
			return None
		# Devanagari detection
		if re.search(r"[\u0900-\u097F]", text):
			return "hinglish"
		# Common Hinglish tokens
		if re.search(r"\b(hai|kya|nahi|haan|acha|accha|kripya|batao)\b", text, re.IGNORECASE):
			return "hinglish"
		return "english"

	def _msg(self, session_state: ConversationSession, key: str) -> str:
		lang = session_state.language or "english"
		messages: dict[str, dict[str, str]] = {
			"ask_description": {
				"english": "Please describe the product (material, size, color, special features).",
				"hinglish": "Product ka short description de dijiye (material, size, color, special features).",
			},
			"ask_image": {
				"english": "Please send a product image first.",
				"hinglish": "Pehle product ki image bhejiye.",
			},
			"ask_better_image": {
				"english": "Your photo is too small or unclear. Please send a clearer image.",
				"hinglish": "Photo thoda unclear hai. Please ek clearer image bhejiye.",
			},
			"ask_blur_choice": {
				"english": "Your image looks blurry. I enhanced it and sent a preview. Can I proceed with this or will you send another image?",
				"hinglish": "Image thoda blurry hai. Maine enhance karke preview bhej diya hai. Iske saath proceed karun ya aap dusri image bhejenge?",
			},
			"ask_low_quality_choice": {
				"english": "Your image is low quality. I enhanced it and sent a preview. Can I proceed with this or will you send another image?",
				"hinglish": "Image low quality hai. Maine enhance karke preview bhej diya hai. Iske saath proceed karun ya aap dusri image bhejenge?",
			},
			"ask_dimensions": {
				"english": "What are the approximate dimensions (L x W x H)?",
				"hinglish": "Approx dimensions kya hain (L x W x H)?",
			},
			"ask_materials": {
				"english": "What material is it made of?",
				"hinglish": "Yeh kis material ka bana hai?",
			},
			"summary_prompt": {
				"english": "Here is what I understood. Reply 'ok' or add corrections:",
				"hinglish": "Maine yeh samjha. Reply 'ok' ya corrections bhejiye:",
			},
			"ack_proceed": {
				"english": "Proceeding with the current image. Please add a short description.",
				"hinglish": "Isi image ke saath proceed kar raha hun. Short description bhejiye.",
			},
			"send_new_image": {
				"english": "Please send another image when you can.",
				"hinglish": "Jab convenient ho, ek aur image bhej dijiye.",
			},
			"listing_confirmed": {
				"english": "Great! I will proceed with listing.",
				"hinglish": "Great! Main listing ke liye proceed kar raha hun.",
			},
		}
		return messages.get(key, {}).get(lang, messages.get(key, {}).get("english", ""))

	async def _handle_media(self, message, session_state: ConversationSession, session: AsyncSession) -> list[ConversationReply]:
		from ..agents.ingestion import ingest_twilio_message

		# Reset pending action on new image
		session_state.pending_action = None

		result = await ingest_twilio_message(message, session, self.settings)
		if not result.product_id:
			session_state.pending_action = "await_better_image"
			return [ConversationReply(body=self._msg(session_state, "ask_better_image"))]

		product = await session.get(Product, result.product_id)
		session_state.product_id = product.id if product else None

		if result.response_key == "image_too_small":
			if product and product.image_url_enhanced:
				preview_url = product.image_url_enhanced
				if preview_url.startswith("s3://"):
					storage = StorageService(self.settings)
					preview_url = storage.presign_s3_url(preview_url, expires_in=3600)
				session_state.pending_action = "low_quality_choice"
				return [
					ConversationReply(body="Enhanced preview attached.", media_url=preview_url),
					ConversationReply(body=self._msg(session_state, "ask_low_quality_choice")),
				]
			session_state.pending_action = "await_better_image"
			return [ConversationReply(body=self._msg(session_state, "ask_better_image"))]

		is_blurry = bool(product and product.attributes and product.attributes.get("is_blurry"))
		if is_blurry and product and product.image_url_enhanced:
			preview_url = product.image_url_enhanced
			if preview_url.startswith("s3://"):
				storage = StorageService(self.settings)
				preview_url = storage.presign_s3_url(preview_url, expires_in=3600)
			session_state.pending_action = "blur_choice"
			return [
				ConversationReply(body="Enhanced preview attached.", media_url=preview_url),
				ConversationReply(body=self._msg(session_state, "ask_blur_choice")),
			]

		session_state.pending_action = "await_description"
		return [ConversationReply(body=self._msg(session_state, "ask_description"))]

	async def _handle_text(self, text: str, session_state: ConversationSession, session: AsyncSession) -> list[ConversationReply]:
		reply = text.strip().lower()

		if session_state.pending_action == "blur_choice":
			if self._is_proceed_reply(reply):
				session_state.pending_action = "await_description"
				return [ConversationReply(body=self._msg(session_state, "ack_proceed"))]
			session_state.pending_action = "await_better_image"
			return [ConversationReply(body=self._msg(session_state, "send_new_image"))]

		if session_state.pending_action == "low_quality_choice":
			if self._is_proceed_reply(reply):
				session_state.pending_action = "await_description"
				return [ConversationReply(body=self._msg(session_state, "ack_proceed"))]
			session_state.pending_action = "await_better_image"
			return [ConversationReply(body=self._msg(session_state, "send_new_image"))]

		if session_state.pending_action == "await_better_image":
			if self._is_proceed_reply(reply) and session_state.product_id:
				session_state.pending_action = "await_description"
				return [ConversationReply(body=self._msg(session_state, "ack_proceed"))]
			return [ConversationReply(body=self._msg(session_state, "send_new_image"))]

		if session_state.pending_action == "confirm_summary":
			if reply in {"ok", "yes", "looks good", "perfect", "done"}:
				session_state.pending_action = None
				return [ConversationReply(body=self._msg(session_state, "listing_confirmed"))]
			# treat as corrections
			state = session_state.state_json or {}
			existing = state.get("description", "")
			combined = (existing + "\n" + text).strip() if existing else text
			state["description"] = combined
			session_state.state_json = state
			product = await session.get(Product, session_state.product_id) if session_state.product_id else None
			if not product:
				session_state.pending_action = "await_better_image"
				return [ConversationReply(body=self._msg(session_state, "send_new_image"))]
			attributes, confidence = await self._run_extraction(session, product, combined)
			attributes = self._apply_attribute_overrides(attributes, state)
			confidence = self._apply_confidence_overrides(confidence, state)
			product.attributes = attributes
			summary = self._format_summary(attributes, session_state)
			return [
				ConversationReply(body=self._msg(session_state, "summary_prompt")),
				ConversationReply(body=summary),
			]

		if session_state.pending_action in {"await_description", "ask_dimensions", "ask_materials"}:
			# Append extra details
			state = session_state.state_json or {}
			if session_state.pending_action in {"ask_dimensions", "ask_materials"}:
				state, answered = self._extract_followup_answer(session_state.pending_action, text, state)
				if not answered:
					state = self._mark_skipped(session_state.pending_action, text, state)
			existing = state.get("description", "")
			combined = (existing + "\n" + text).strip() if existing else text
			state["description"] = combined
			session_state.state_json = state

			product = await session.get(Product, session_state.product_id) if session_state.product_id else None
			if not product:
				session_state.pending_action = "await_better_image"
				return [ConversationReply(body=self._msg(session_state, "send_new_image"))]

			attributes, confidence = await self._run_extraction(session, product, combined)
			attributes = self._apply_attribute_overrides(attributes, state)
			confidence = self._apply_confidence_overrides(confidence, state)
			product.attributes = attributes
			state["last_attributes"] = attributes
			session_state.state_json = state
			followup = self._pick_followup_question(confidence, state)
			if followup:
				session_state.pending_action = followup
				return [ConversationReply(body=self._msg(session_state, followup))]
			session_state.pending_action = "confirm_summary"
			summary = self._format_summary(attributes, session_state)
			return [
				ConversationReply(body=self._msg(session_state, "summary_prompt")),
				ConversationReply(body=summary),
			]

		if not session_state.product_id:
			return [ConversationReply(body=self._msg(session_state, "ask_image"))]

		# Default fallback
		session_state.pending_action = "await_description"
		return [ConversationReply(body=self._msg(session_state, "ask_description"))]

	async def _run_extraction(
		self,
		session: AsyncSession,
		product: Product,
		description: str,
	) -> tuple[dict[str, Any], dict[str, float]]:
		image_url = product.image_url_enhanced or product.image_url
		if not image_url:
			return {}, {}
		storage = StorageService(self.settings)
		image_bytes = await storage.download_bytes_from_url(image_url)
		mime_type = "image/jpeg"
		service = GeminiService(self.settings)
		attributes, confidence = await service.extract_attributes(
			image_bytes=image_bytes,
			mime_type=mime_type,
			user_description=description,
			transcription=product.transcript or "",
		)
		product.attributes = attributes
		product.user_provided_description = description
		product.extraction_confidence = sum(confidence.values()) / max(len(confidence.values()), 1)
		await log_event(
			session=session,
			agent="conversation_extraction",
			action="extract_attributes",
			input_data={"product_id": str(product.id), "description": description},
			output_data={"attributes": attributes, "confidence": confidence},
			product_id=product.id,
		)
		return attributes, confidence

	def _pick_followup_question(self, confidence: dict[str, float], state: dict[str, Any]) -> str | None:
		if not confidence:
			return None
		if not state.get("answered_dimensions") and not state.get("skipped_dimensions") and confidence.get("dimensions", 1.0) < 0.7:
			return "ask_dimensions"
		if not state.get("answered_materials") and not state.get("skipped_materials") and confidence.get("materials", 1.0) < 0.7:
			return "ask_materials"
		return None

	def _format_summary(self, attributes: dict[str, Any], session_state: ConversationSession) -> str:
		materials = attributes.get("materials") or []
		if isinstance(materials, str):
			materials = [materials]
		lines = [
			f"Name: {attributes.get('name', '')}",
			f"Category: {attributes.get('category', '')}",
			f"Materials: {', '.join(materials)}",
			f"Dimensions: {attributes.get('dimensions', '')}",
			f"Description: {attributes.get('description', '')}",
		]
		return "\n".join([line for line in lines if line.strip()])

	def _is_proceed_reply(self, reply: str) -> bool:
		if reply in {"proceed", "ok", "okay", "yes", "y", "continue"}:
			return True
		keywords = ["use this", "same image", "only image", "use this image", "go with this"]
		return any(keyword in reply for keyword in keywords)

	def _apply_attribute_overrides(self, attributes: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
		if state.get("dimensions_value"):
			attributes["dimensions"] = state["dimensions_value"]
		elif state.get("dimensions_raw"):
			attributes["dimensions"] = {"raw": state["dimensions_raw"]}
		if state.get("materials_value"):
			attributes["materials"] = state["materials_value"]
		elif state.get("materials_raw"):
			attributes["materials"] = [state["materials_raw"]]
		return attributes

	def _apply_confidence_overrides(self, confidence: dict[str, float], state: dict[str, Any]) -> dict[str, float]:
		if state.get("answered_dimensions") and not state.get("skipped_dimensions"):
			confidence["dimensions"] = 1.0
		if state.get("answered_materials") and not state.get("skipped_materials"):
			confidence["materials"] = 1.0
		return confidence

	def _extract_followup_answer(
		self,
		action: str,
		text: str,
		state: dict[str, Any],
	) -> tuple[dict[str, Any], bool]:
		if action == "ask_dimensions":
			dimensions = self._parse_dimensions(text)
			if dimensions:
				state["answered_dimensions"] = True
				state["dimensions_value"] = dimensions
				state["dimensions_raw"] = text.strip()
				return state, True
			return state, False
		if action == "ask_materials":
			materials = self._parse_materials(text)
			if materials:
				state["answered_materials"] = True
				state["materials_value"] = materials
				state["materials_raw"] = text.strip()
				return state, True
			return state, False
		return state, False

	def _mark_skipped(self, action: str, text: str, state: dict[str, Any]) -> dict[str, Any]:
		if action == "ask_dimensions":
			state["skipped_dimensions"] = True
			state["dimensions_raw"] = text.strip()
		elif action == "ask_materials":
			state["skipped_materials"] = True
			state["materials_raw"] = text.strip()
		return state

	def _parse_dimensions(self, text: str) -> dict[str, Any] | None:
		if not text:
			return None
		clean = text.lower()
		unit_map = {
			"inches": "in",
			"inch": "in",
			"feet": "ft",
		}
		def _normalize_unit(unit: str | None) -> str | None:
			if not unit:
				return None
			return unit_map.get(unit, unit)

		def _find_dim(keyword: str) -> tuple[float | None, str | None]:
			match = re.search(rf"\b{keyword}\b\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(cm|mm|in|inch|inches|ft|feet)?", clean)
			if not match:
				return None, None
			value = float(match.group(1))
			unit = _normalize_unit(match.group(2))
			return value, unit

		length, unit_l = _find_dim("length")
		width, unit_w = _find_dim("width")
		height, unit_h = _find_dim("height")
		unit = unit_l or unit_w or unit_h
		if any(value is not None for value in (length, width, height)):
			data = {"length": length, "width": width, "height": height}
			if unit:
				data["unit"] = unit
			return data

		matches = re.findall(r"(\d+(?:\.\d+)?)\s*(cm|mm|in|inch|inches|ft|feet)?", clean)
		if len(matches) < 2:
			return None
		values = [float(value) for value, _ in matches][:3]
		unit = _normalize_unit(next((unit for _, unit in matches if unit), None))
		data = {"length": values[0], "width": values[1]}
		if len(values) > 2:
			data["height"] = values[2]
		if unit:
			data["unit"] = unit
		return data

	def _parse_materials(self, text: str) -> list[str]:
		clean = text.lower().replace("&", "and")
		parts = re.split(r"[,/]|\band\b", clean)
		stopwords = {
			"made",
			"of",
			"material",
			"materials",
			"is",
			"it",
			"a",
			"the",
			"this",
			"that",
			"why",
			"required",
			"need",
			"to",
			"for",
		}
		materials: list[str] = []
		for part in parts:
			tokens = [token for token in re.split(r"\s+", part.strip()) if token]
			filtered = [token for token in tokens if token not in stopwords]
			value = " ".join(filtered).strip()
			if value:
				materials.append(value)
		seen: set[str] = set()
		result: list[str] = []
		for item in materials:
			if item not in seen:
				seen.add(item)
				result.append(item)
		return result
