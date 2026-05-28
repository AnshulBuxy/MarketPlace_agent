from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models.conversation_session import ConversationSession
from ..models.enums import MessageType
from ..models.product import Product
from ..services.llm import GeminiChatService, GeminiService
from ..services.speech import SpeechService
from ..services.storage import StorageService
from ..services.whatsapp import (
	parse_twilio_payload,
	TwilioMedia,
	send_twilio_whatsapp_media_message,
	send_twilio_whatsapp_message,
)
from ..utils.http import fetch_bytes
from ..utils.audit import log_event

logger = logging.getLogger(__name__)


@dataclass
class ConversationReply:
	body: str
	media_url: str | None = None


@dataclass
class AgentDecision:
	action: str
	reply: str
	language: str
	update_description: str | None
	needs_extraction: bool


class ConversationAgent:
	"""LLM-based conversation agent."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._chat = GeminiChatService(settings)

	async def plan(self, context: dict[str, Any]) -> AgentDecision:
		logger.info(f"[CONVERSATION_AGENT] Input context: user_msg={context.get('user_message', '')[:50]}... has_image={context.get('has_image')} quality={context.get('image_quality')}")
		payload = await self._chat.generate_json(self._build_prompt(context))
		decision = AgentDecision(
			action=str(payload.get("action", "request_image")),
			reply=str(payload.get("reply", "")),
			language=str(payload.get("language", "english")),
			update_description=payload.get("update_description") or None,
			needs_extraction=bool(payload.get("needs_extraction", False)),
		)
		logger.info(f"[CONVERSATION_AGENT] Decision: action={decision.action} lang={decision.language} needs_extraction={decision.needs_extraction} model=gemini-2.0-flash")
		return decision

	def _build_prompt(self, context: dict[str, Any]) -> str:
		return (
			"You are a helpful WhatsApp assistant for marketplace product intake. "
			"Reply in simple, natural Hinglish unless the user clearly writes in English. "
			"Keep the tone warm, human, and concise, like a real WhatsApp chat. "
			"Use Roman Hindi mixed with English, and it is okay to add a light emoji occasionally. "
			"Avoid formal wording. Prefer lines like: 'Hii, aapka product receive ho gaya hai 😊', "
			"'Sab sahi hai, koi changes nahi karna', '800 rs ke aas paas', 'Photo thodi clear bhejiye'. "
			"When asking for a number or a choice, make it sound natural and polite. "
			"Return ONLY valid JSON with keys: action, reply, language, update_description, needs_extraction. "
			"language must be english or hinglish. "
			"action must be one of: request_image, request_clear_image, extract_and_summarize, confirm_summary, acknowledge. "
			"If there is no usable image, action=request_image. "
			"If image_quality is too_small or blurry, action=request_clear_image. "
			"If image is available, action=extract_and_summarize and needs_extraction=true. "
			"When extract_and_summarize, include {SUMMARY} in reply and ask for corrections in Hinglish like: 'Sab sahi hai ya kuch change karna hai?'. "
			"If user is correcting, keep action=extract_and_summarize and set update_description to the correction text. "
			"Do not include any extra text.\n\n"
			f"user_message: {context.get('user_message','')}\n"
			f"has_image: {context.get('has_image')}\n"
			f"image_quality: {context.get('image_quality','')}\n"
			f"existing_description: {context.get('description','')}\n"
			f"language_hint: {context.get('language','english')}\n"
			f"last_summary_sent: {context.get('summary_sent', False)}\n"
		)


class ExtractionAgent:
	"""Multimodal extraction agent."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._extractor = GeminiService(settings)

	async def run(self, session: AsyncSession, product: Product, description: str) -> tuple[dict[str, Any], dict[str, float]]:
		logger.info(f"[EXTRACTION_AGENT] Starting extraction: product_id={product.id} description={description[:50]}...")
		image_url = product.image_url_enhanced or product.image_url
		if not image_url:
			logger.warning(f"[EXTRACTION_AGENT] No image URL found for product {product.id}")
			return {}, {}
		storage = StorageService(self._settings)
		image_bytes = await storage.download_bytes_from_url(image_url)
		logger.info(f"[EXTRACTION_AGENT] Image downloaded: {len(image_bytes)} bytes, calling Gemini multimodal...")
		attributes, confidence = await self._extractor.extract_attributes(
			image_bytes=image_bytes,
			mime_type="image/jpeg",
			user_description=description,
			transcription=product.transcript or "",
		)
		logger.info(f"[EXTRACTION_AGENT] Extraction complete: {len(attributes)} attributes extracted, avg_confidence={sum(confidence.values()) / max(len(confidence.values()), 1):.2f} model=gemini-2.0-flash")
		logger.info(f"[EXTRACTION_AGENT] Attributes: {list(attributes.keys())}")
		product.attributes = attributes
		product.user_provided_description = description
		product.extraction_confidence = sum(confidence.values()) / max(len(confidence.values()), 1)
		await log_event(
			session=session,
			agent="multiagent_extraction",
			action="extract_attributes",
			input_data={"product_id": str(product.id), "description": description},
			output_data={"attributes": attributes, "confidence": confidence},
			product_id=product.id,
		)
		return attributes, confidence


class MultiAgentManager:
	"""Supervisor for multi-agent conversation flow."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._conversation_agent = ConversationAgent(settings)
		self._extraction_agent = ExtractionAgent(settings)

	async def handle_payload(self, payload: dict, session: AsyncSession) -> list[ConversationReply]:
		message = parse_twilio_payload(payload)
		logger.info(f"[MULTIAGENT_MANAGER] Processing message from {message.from_number} media={bool(message.media)} text={message.body[:50] if message.body else 'None'}...")
		session_state = await self._get_or_create_session(session, message.from_number)

		product = None
		state = session_state.state_json or {}
		image_quality = state.get("last_image_quality", "")
		message_type = MessageType.TEXT
		message_text = message.body or ""
		if message.media:
			if any(media.is_image() for media in message.media):
				from ..agents.ingestion import ingest_twilio_message

				logger.info(f"[INGESTION_AGENT] Starting media ingestion...")
				result = await ingest_twilio_message(message, session, self._settings)
				message_type = result.message_type
				if result.product_id:
					product = await session.get(Product, result.product_id)
					session_state.product_id = product.id if product else None
					image_quality = self._normalize_quality(result.response_key)
					logger.info(f"[INGESTION_AGENT] Product created: id={product.id} quality={image_quality}")
				else:
					image_quality = self._normalize_quality(result.response_key)
					logger.warning(f"[INGESTION_AGENT] Ingestion failed: {result.response_key}")
			elif all(media.is_audio() for media in message.media):
				message_type = MessageType.AUDIO
				message_text = await self._transcribe_audio_message(message.media[0]) or ""
				if message_text:
					logger.info(f"[MULTIAGENT_MANAGER] Transcribed audio follow-up: {message_text[:120]}...")
				if session_state.product_id:
					product = await session.get(Product, session_state.product_id)
			else:
				# Keep the existing text flow intact for any other media types.
				pass

		if session_state.product_id and not product:
			product = await session.get(Product, session_state.product_id)

		transcript = product.transcript if product and product.transcript else ""
		if not message_text:
			message_text = transcript

		language = self._detect_language(message_text)
		if language:
			session_state.language = language
			logger.info(f"[MULTIAGENT_MANAGER] Detected language: {language}")

		if image_quality:
			state["last_image_quality"] = image_quality
		context = {
			"user_message": message_text,
			"has_image": bool(product and (product.image_url or product.image_url_enhanced)),
			"image_quality": image_quality,
			"description": state.get("description", ""),
			"language": session_state.language or "english",
			"summary_sent": state.get("summary_sent", False),
		}

		logger.info(f"[MULTIAGENT_MANAGER] Calling ConversationAgent...")
		decision = await self._conversation_agent.plan(context)
		if decision.language:
			session_state.language = decision.language

		if decision.update_description:
			state["description"] = self._merge_description(state.get("description", ""), decision.update_description)

		replies: list[ConversationReply] = []
		if decision.action in {"request_image", "request_clear_image"}:
			logger.info(f"[MULTIAGENT_MANAGER] Agent action: {decision.action} (requesting image)")
			replies.append(ConversationReply(body=decision.reply or self._default_reply(decision.action)))
			session_state.state_json = state
			await session.flush()
			return replies

		if decision.needs_extraction and product:
			logger.info(f"[MULTIAGENT_MANAGER] Agent action: extract_and_summarize (calling ExtractionAgent)")
			description = state.get("description", "")
			attributes, confidence = await self._extraction_agent.run(session, product, description)
			summary = self._format_summary(attributes)
			state["last_attributes"] = attributes
			state["summary_sent"] = True
			state["last_summary"] = summary
			session_state.state_json = state
			logger.info(f"[MULTIAGENT_MANAGER] Summary formatted, sending {len(self._build_summary_replies(decision.reply, summary))} reply/replies to user")
			replies.extend(self._build_summary_replies(decision.reply, summary))
			await session.flush()
			return replies

		logger.info(f"[MULTIAGENT_MANAGER] Agent action: acknowledge (simple reply)")
		replies.append(ConversationReply(body=decision.reply or ""))
		session_state.state_json = state
		await session.flush()
		return replies

	async def _transcribe_audio_message(self, media: TwilioMedia) -> str | None:
		"""Transcribe an inbound audio message without creating a new product."""
		audio_bytes = await fetch_bytes(
			media.url,
			auth=(self._settings.twilio_account_sid, self._settings.twilio_auth_token) if self._settings.twilio_account_sid and self._settings.twilio_auth_token else None,
			timeout_seconds=self._settings.http_timeout_seconds,
			max_retries=self._settings.http_max_retries,
		)
		speech = SpeechService(self._settings)
		content_type = media.content_type or "audio/mpeg"
		ext = content_type.split("/")[-1] or "mp3"
		return await speech.transcribe_audio(audio_bytes, filename=f"audio.{ext}", content_type=content_type)

	async def send_replies(self, to_number: str, replies: list[ConversationReply]) -> None:
		for reply in replies:
			if reply.media_url:
				await send_twilio_whatsapp_media_message(
					self._settings,
					to_number=to_number,
					body=reply.body,
					media_url=reply.media_url,
				)
			else:
				await send_twilio_whatsapp_message(
					self._settings,
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
		if re.search(r"[\u0900-\u097F]", text):
			return "hinglish"
		if re.search(r"\b(hai|kya|nahi|haan|acha|accha|kripya|batao)\b", text, re.IGNORECASE):
			return "hinglish"
		return "english"

	@staticmethod
	def _merge_description(existing: str, update: str) -> str:
		if not existing:
			return update.strip()
		return (existing + "\n" + update).strip()

	@staticmethod
	def _format_summary(attributes: dict[str, Any]) -> str:
		materials = attributes.get("materials") or []
		if isinstance(materials, str):
			materials = [materials]
		lines = [
			f"Naam: {attributes.get('name', '')}",
			f"Category: {attributes.get('category', '')}",
			f"Materials: {', '.join(materials)}",
			f"Dimensions: {attributes.get('dimensions', '')}",
			f"Description: {attributes.get('description', '')}",
		]
		summary = "\n".join([line for line in lines if line.strip()])
		return f"Maine yeh samjha:\n{summary}"

	@staticmethod
	def _build_summary_replies(reply: str, summary: str) -> list[ConversationReply]:
		if not reply:
			return [ConversationReply(body=summary)]
		if "{SUMMARY}" in reply:
			return [ConversationReply(body=reply.replace("{SUMMARY}", summary))]
		return [ConversationReply(body=reply), ConversationReply(body=summary)]

	@staticmethod
	def _default_reply(action: str) -> str:
		if action == "request_clear_image":
			return "Photo thodi clear bhejiye, phir main product ko sahi se bata dunga 😊"
		return "Pehle product ki image bhejiye, phir main aage badhunga 😊"

	@staticmethod
	def _normalize_quality(response_key: str) -> str:
		if response_key == "image_too_small":
			return "too_small"
		if response_key == "image_blurry":
			return "blurry"
		return "ok"
