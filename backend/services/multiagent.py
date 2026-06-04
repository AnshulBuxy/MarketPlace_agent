from __future__ import annotations

import copy
import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from ..config import Settings
from ..models.conversation_session import ConversationSession
from ..models.product import Product
from ..services.llm import GeminiChatService, GeminiService, _normalize_attributes
from ..services.speech import SpeechService
from ..services.storage import StorageService
from ..services.whatsapp import (
    parse_meta_payload,
    WhatsAppMedia,
    get_media_bytes,
    send_meta_whatsapp_media_message,
    send_meta_whatsapp_message,
    # backward-compat aliases kept for any remaining call sites
    parse_twilio_payload,
    TwilioMedia,
    send_twilio_whatsapp_media_message,
    send_twilio_whatsapp_message,
)
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


# ---------------------------------------------------------------------------
# Conversation phases — used to drive deterministic action selection
# ---------------------------------------------------------------------------
# request_image      : no usable image in session yet
# request_clear_image: image was blurry / too small
# extract_and_summarize: good image, first extraction
# correction         : summary already shown, user is editing
# done               : user confirmed, no more changes


class ConversationAgent:
    """LLM-based agent that generates Hinglish/English replies for a given phase."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._chat = GeminiChatService(settings)

    async def plan(self, context: dict[str, Any]) -> AgentDecision:
        logger.info(
            "[CONVERSATION_AGENT] phase=%s user_msg=%.50s has_image=%s",
            context.get("phase"),
            context.get("user_message", ""),
            context.get("has_image"),
        )
        payload = await self._chat.generate_json(self._build_prompt(context))
        decision = AgentDecision(
            action=str(payload.get("action", "request_image")),
            reply=str(payload.get("reply", "")),
            language=str(payload.get("language", context.get("language", "hinglish"))),
            update_description=payload.get("update_description") or None,
            needs_extraction=bool(payload.get("needs_extraction", False)),
        )
        logger.info(
            "[CONVERSATION_AGENT] action=%s lang=%s needs_extraction=%s",
            decision.action,
            decision.language,
            decision.needs_extraction,
        )
        return decision

    def _build_prompt(self, context: dict[str, Any]) -> str:
        phase = context.get("phase", "request_image")
        language = context.get("language", "hinglish")
        user_message = context.get("user_message", "")
        description = context.get("description", "")
        last_summary = context.get("last_summary", "")

        base = (
            "You are a friendly WhatsApp assistant helping artisans list their handmade products. "
            "Always reply in warm, natural Hinglish (Roman Hindi mixed with English) "
            "UNLESS the user's message is clearly in English — then reply in English. "
            "Keep messages short and conversational, like a real WhatsApp chat. A light emoji is fine. "
            "Return ONLY valid JSON — no markdown fences, no extra text. "
            'Keys: "action" (string), "reply" (string), "language" ("hinglish"|"english"), '
            '"update_description" (string|null), "needs_extraction" (boolean).\n'
            "CRITICAL: The 'reply' value must be the exact message sent to the user — "
            "NO internal reasoning, NO language notes, NO meta-commentary. "
            "Just the natural friendly response text, nothing else.\n\n"
            f'user_message: "{user_message}"\n'
            f'session_language: "{language}"\n'
        )

        if phase == "request_image":
            instructions = (
                "\nPHASE: request_image — the user has not sent a product image yet.\n"
                "If this is a greeting (hi, hello, hii, hey, etc.), welcome them warmly and ask for their product photo.\n"
                "action = 'request_image', needs_extraction = false, update_description = null.\n"
                "Example reply (hinglish): "
                "'Hii! Banao mein aapka swagat hai 😊 Apne product ki ek achhi photo bhejiye, "
                "main sab details nikal dunga!'"
            )

        elif phase == "request_clear_image":
            instructions = (
                "\nPHASE: request_clear_image — the image received was blurry or too small.\n"
                "Politely ask for a clearer photo. Suggest good lighting and a steady hand.\n"
                "action = 'request_clear_image', needs_extraction = false, update_description = null.\n"
                "Example reply (hinglish): "
                "'Photo thodi blurry aa gayi 😊 Ek baar aur try karein — "
                "achhi roshni mein aur seedhi photo lein, main sahi se details nikal dunga!'"
            )

        elif phase == "extract_and_summarize":
            instructions = (
                "\nPHASE: extract_and_summarize — a good product image is available, extracting details for the first time.\n"
                "Tell the user you received their photo and are showing the extracted details.\n"
                "Include the literal text {SUMMARY} in your reply exactly where the product summary should appear.\n"
                "After the summary placeholder, ask if everything is correct or if anything needs changing.\n"
                "action = 'extract_and_summarize', needs_extraction = true, update_description = null.\n"
                "Example reply (hinglish): "
                "'Aapka photo mil gaya hai, ab aapke product ki details yeh hain 😊\n\n{SUMMARY}\n\nSab sahi hai ya kuch badalna hai?'"
            )

        elif phase == "correction":
            instructions = (
                "\nPHASE: correction — the user has already seen the product summary and is responding.\n"
                f'Previous summary (truncated): "{last_summary[:300] if last_summary else "N/A"}"\n'
                f'Existing description: "{description[:200] if description else "N/A"}"\n'
                "\nDecide based on the user's message:\n"
                "A) If user says something like 'sab sahi hai', 'ok', 'theek hai', 'done', 'no changes', 'perfect' "
                "— they are satisfied. action = 'acknowledge', needs_extraction = false, update_description = null. "
                "Reply telling them their details have been noted and you will contact them soon. "
                "Example (hinglish): 'Shukriya! Humne aapke product ki details note kar li hain 😊 Hum aapko jald hi contact karenge!'\n"
                "B) If user provides any correction or change request "
                "— extract the correction into update_description. "
                "action = 'extract_and_summarize', needs_extraction = true. "
                "Include {SUMMARY} in reply. "
                "Example reply: 'Done! Updated details yeh hain:\n\n{SUMMARY}\n\nAur kuch badalna hai?'\n"
            )

        else:
            instructions = (
                "\nRespond helpfully. action = 'acknowledge', needs_extraction = false.\n"
            )

        return base + instructions


class ExtractionAgent:
    """Multimodal extraction agent."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._extractor = GeminiService(settings)

    async def run(
        self,
        session: AsyncSession,
        product: Product,
        description: str,
    ) -> tuple[dict[str, Any], dict[str, float]]:
        logger.info(
            "[EXTRACTION_AGENT] product_id=%s desc=%.50s",
            product.id,
            description,
        )
        image_url = product.image_url or product.image_url_enhanced
        if not image_url:
            logger.warning("[EXTRACTION_AGENT] No image URL for product %s", product.id)
            return {}, {}

        storage = StorageService(self._settings)
        image_bytes = await storage.download_bytes_from_url(image_url)
        logger.info("[EXTRACTION_AGENT] Image downloaded: %d bytes", len(image_bytes))

        attributes, confidence = await self._extractor.extract_attributes(
            image_bytes=image_bytes,
            mime_type="image/jpeg",
            user_description=description,
            transcription=product.transcript or "",
        )
        logger.info(
            "[EXTRACTION_AGENT] Done: %d attrs avg_conf=%.2f",
            len(attributes),
            sum(confidence.values()) / max(len(confidence.values()), 1),
        )

        product.attributes = attributes
        product.user_provided_description = description
        product.extraction_confidence = (
            sum(confidence.values()) / max(len(confidence.values()), 1)
        )
        await log_event(
            session=session,
            agent="multiagent_extraction",
            action="extract_attributes",
            input_data={"product_id": str(product.id), "description": description},
            output_data={"attributes": attributes, "confidence": confidence},
            product_id=product.id,
        )
        return attributes, confidence


class GroqEditAgent:
    """Text-only agent that edits existing product attributes via Groq.

    Called on every correction turn so Gemini vision is never re-invoked
    after the first extraction.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._chat = GeminiChatService(settings)  # Groq primary, Gemini fallback

    async def apply_correction(
        self,
        existing_attributes: dict[str, Any],
        user_correction: str,
    ) -> dict[str, Any]:
        """Return updated attributes with only the user-requested fields changed."""
        # Strip internal tracking keys before sending to LLM
        attrs_clean = {
            k: v for k, v in existing_attributes.items()
            if k not in ("info_source",)
        }

        prompt = (
            "You are a product listing editor for Indian artisan products.\n"
            "The artisan has reviewed their product details and wants to update specific fields.\n\n"
            "Current product details (JSON):\n"
            f"{json.dumps(attrs_clean, indent=2, ensure_ascii=False)}\n\n"
            f'Artisan\'s correction: "{user_correction}"\n\n'
            "Rules:\n"
            "1. Understand what field(s) the artisan wants to change.\n"
            "2. Update ONLY those fields. Keep every other field exactly as-is.\n"
            "3. Return ONLY valid JSON — no markdown, no extra text.\n"
            "4. JSON must have: name (string), category (string), "
            "materials (array of strings), "
            "dimensions (object with length/width/height/unit keys, or a 'note' key for text), "
            "description (string), tags (array of strings).\n"
        )

        logger.info("[GROQ_EDIT] Applying correction: %.100s", user_correction)
        raw = await self._chat.generate_json(prompt)
        updated = _normalize_attributes(raw)
        updated["info_source"] = "groq_edit"
        logger.info("[GROQ_EDIT] Done. Changed fields visible in updated attrs.")
        print(f"[GROQ_EDIT] Before: {attrs_clean.get('name')!r}  After: {updated.get('name')!r}")
        return updated


class MultiAgentManager:
    """Supervisor for multi-agent conversation flow."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._conversation_agent = ConversationAgent(settings)
        self._extraction_agent = ExtractionAgent(settings)
        self._edit_agent = GroqEditAgent(settings)

    async def handle_payload(
        self, payload: dict, session: AsyncSession
    ) -> list[ConversationReply]:
        message = parse_twilio_payload(payload)
        logger.info(
            "[MULTIAGENT] from=%s media=%s text=%.50s",
            message.from_number,
            bool(message.media),
            message.body or "",
        )

        session_state = await self._get_or_create_session(session, message.from_number)
        # deepcopy ensures state is always a NEW object — avoids SQLAlchemy's
        # "same-reference = no change" optimisation that silently skips the UPDATE.
        state: dict[str, Any] = copy.deepcopy(session_state.state_json) if session_state.state_json else {}
        print(
            f"[STATE] Loaded: phone={message.from_number} "
            f"product_id={session_state.product_id} "
            f"summary_sent={state.get('summary_sent')} "
            f"has_last_attrs={bool(state.get('last_attributes'))} "
            f"lang={session_state.language}"
        )

        product: Product | None = None
        is_new_image = False
        fresh_image_quality = ""
        message_text = message.body or ""

        # ── Media handling ──────────────────────────────────────────────────
        if message.media:
            if any(media.is_image() for media in message.media):
                from ..agents.ingestion import ingest_twilio_message

                logger.info("[MULTIAGENT] Image received — ingesting")
                result = await ingest_twilio_message(message, session, self._settings)

                if result.product_id:
                    product = await session.get(Product, result.product_id)
                    session_state.product_id = product.id if product else None
                    fresh_image_quality = self._normalize_quality(result.response_key)
                    is_new_image = True
                    # New image resets the summary state
                    state.pop("summary_sent", None)
                    state.pop("last_summary", None)
                    state.pop("last_image_quality", None)
                    if fresh_image_quality != "ok":
                        state["last_image_quality"] = fresh_image_quality
                    logger.info(
                        "[MULTIAGENT] Product created id=%s quality=%s",
                        product.id if product else None,
                        fresh_image_quality,
                    )
                else:
                    fresh_image_quality = self._normalize_quality(result.response_key)
                    state["last_image_quality"] = fresh_image_quality
                    logger.warning("[MULTIAGENT] Ingestion failed: %s", result.response_key)

            elif all(media.is_audio() for media in message.media):
                logger.info("[MULTIAGENT] Audio received — transcribing")
                message_text = (
                    await self._transcribe_audio_message(message.media[0]) or ""
                )
                if message_text:
                    logger.info("[MULTIAGENT] Transcribed: %.120s", message_text)
                if session_state.product_id:
                    product = await session.get(Product, session_state.product_id)

        # ── Load existing product if not loaded yet ──────────────────────────
        if session_state.product_id and not product:
            product = await session.get(Product, session_state.product_id)

        # ── Language detection ───────────────────────────────────────────────
        detected = self._detect_language(message_text)
        if detected:
            session_state.language = detected
        if not session_state.language:
            session_state.language = "hinglish"

        # ── Determine conversation phase (deterministic) ────────────────────
        has_usable_image = bool(
            product and (product.image_url or product.image_url_enhanced)
        )
        phase = self._determine_phase(
            state, has_usable_image, is_new_image, fresh_image_quality
        )
        print(
            f"[PHASE] → {phase} | has_image={has_usable_image} "
            f"is_new_image={is_new_image} summary_sent={state.get('summary_sent')}"
        )
        logger.info("[MULTIAGENT] Phase: %s has_image=%s", phase, has_usable_image)

        # ── Build context for ConversationAgent ─────────────────────────────
        context = {
            "user_message": message_text,
            "has_image": has_usable_image,
            "image_quality": fresh_image_quality if is_new_image else "",
            "description": state.get("description", ""),
            "language": session_state.language,
            "summary_sent": state.get("summary_sent", False),
            "phase": phase,
            "last_summary": state.get("last_summary", ""),
        }

        decision = await self._conversation_agent.plan(context)

        # Sync language back
        if decision.language:
            session_state.language = decision.language

        # Accumulate user corrections into description
        if decision.update_description:
            state["description"] = self._merge_description(
                state.get("description", ""), decision.update_description
            )

        # ── Route based on phase ────────────────────────────────────────────
        replies: list[ConversationReply] = []

        if phase in ("request_image", "request_clear_image"):
            replies.append(
                ConversationReply(
                    body=decision.reply or self._default_reply(phase)
                )
            )

        elif phase == "extract_and_summarize":
            # First extraction after a good image — always run it
            if product:
                description = state.get("description", "")
                attributes, _confidence = await self._extraction_agent.run(
                    session, product, description
                )
                summary = self._format_summary(attributes, session_state.language)
                state["last_attributes"] = attributes
                state["summary_sent"] = True
                state["last_summary"] = summary
                replies.extend(self._build_summary_replies(decision.reply, summary))
            else:
                replies.append(ConversationReply(body=self._default_reply("request_image")))

        elif phase == "correction":
            # Rule-based confirmation wins over LLM (more reliable for short phrases)
            user_confirmed = self._is_user_confirming(message_text) or (
                decision.action == "acknowledge"
                or not decision.needs_extraction
            )
            logger.info("[MULTIAGENT] correction: confirmed=%s msg=%.50s", user_confirmed, message_text)
            if user_confirmed:
                logger.info("[MULTIAGENT] User confirmed — conversation done")
                replies.append(
                    ConversationReply(
                        body=decision.reply or self._done_reply(session_state.language)
                    )
                )
            elif product:
                # ── Groq edits existing JSON — no Gemini / no image re-download ──
                logger.info("[MULTIAGENT] User gave corrections — calling GroqEditAgent")
                existing_attrs = state.get("last_attributes") or {}
                correction_text = decision.update_description or message_text
                print(f"[GROQ_EDIT] existing_attrs keys={list(existing_attrs.keys())} correction={correction_text!r}")

                updated_attrs = await self._edit_agent.apply_correction(
                    existing_attributes=existing_attrs,
                    user_correction=correction_text,
                )
                product.attributes = updated_attrs
                summary = self._format_summary(updated_attrs, session_state.language)
                state["last_attributes"] = updated_attrs
                state["last_summary"] = summary

                await log_event(
                    session=session,
                    agent="groq_edit",
                    action="apply_correction",
                    input_data={"correction": correction_text},
                    output_data={"updated_attributes": updated_attrs},
                    product_id=product.id,
                )
                replies.extend(self._build_summary_replies(decision.reply, summary))
            else:
                replies.append(ConversationReply(body=self._default_reply("request_image")))

        else:  # acknowledge / done (fallback)
            replies.append(ConversationReply(body=decision.reply or ""))

        session_state.state_json = state
        # Explicitly mark state_json dirty so SQLAlchemy always writes the UPDATE,
        # even when the dict reference hasn't changed (JSON mutation tracking issue).
        flag_modified(session_state, "state_json")
        await session.flush()
        return replies

    # ── Audio transcription ──────────────────────────────────────────────────

    async def _transcribe_audio_message(self, media: WhatsAppMedia) -> str | None:
        """Transcribe an inbound audio message without creating a new product."""
        # Use pre-downloaded bytes if the webhook handler already fetched them
        if getattr(media, "_bytes", None):
            audio_bytes = media._bytes
        else:
            audio_bytes = await get_media_bytes(media.media_id, self._settings)

        speech = SpeechService(self._settings)
        # Strip codec parameters e.g. "audio/ogg; codecs=opus" → "audio/ogg"
        raw_ct = media.content_type or "audio/ogg"
        content_type = raw_ct.split(";")[0].strip()
        ext = content_type.split("/")[-1] or "ogg"
        result = await speech.transcribe_audio(
            audio_bytes, filename=f"audio.{ext}", content_type=content_type
        )
        print(f"[STT] Whisper transcription: {result!r}")
        return result

    # ── Reply sending (used by callers outside webhook) ──────────────────────

    async def send_replies(
        self, to_number: str, replies: list[ConversationReply]
    ) -> None:
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

    # ── Session helpers ──────────────────────────────────────────────────────

    async def _get_or_create_session(
        self, session: AsyncSession, phone: str
    ) -> ConversationSession:
        state = await session.get(ConversationSession, phone)
        if state:
            # Ensure existing sessions without a language get the default
            if not state.language:
                state.language = "hinglish"
            return state
        state = ConversationSession(
            phone_number=phone, language="hinglish", state_json={}
        )
        session.add(state)
        await session.flush()
        return state

    # ── Language detection ────────────────────────────────────────────────────

    @staticmethod
    def _detect_language(text: str | None) -> str | None:
        """Detect language from text. Returns None for short/ambiguous inputs.
        Default is Hinglish — only switches to English for clearly English-only messages."""
        if not text:
            return None
        # Devanagari script → Hinglish
        if re.search(r"[ऀ-ॿ]", text):
            return "hinglish"
        # Common Hindi / Hinglish words and abbreviations in Roman script → Hinglish
        if re.search(
            r"\b(hai|kya|nahi|nai|haan|haa|acha|accha|kripya|batao|"
            r"mera|tera|uska|iske|isake|iska|iski|unka|unke|inke|inka|"
            r"yeh|woh|wo|aap|main|hum|tum|bhi|aur|par|se|ko|ka|ki|ke|"
            r"ek|do|theek|sahi|shi|thoda|bilkul|zaroor|lekin|phir|abhi|"
            r"baad|pehle|karo|karein|karna|chahiye|lagta|lagti|"
            r"naam|kitna|kitni|kab|kahan|kyun|kyunki|toh|"
            r"hain|tha|thi|raha|rahi|gaya|gayi|"
            r"\bh\b)\b",
            text,
            re.IGNORECASE,
        ):
            return "hinglish"
        # Only switch to English for long, clearly English-only messages (8+ alpha words)
        words = [w for w in text.split() if w.isalpha() and len(w) > 1]
        if len(words) >= 8:
            return "english"
        # Short / ambiguous → keep existing session language (default: hinglish)
        return None

    # ── Phase determination (deterministic, no LLM) ──────────────────────────

    @staticmethod
    def _determine_phase(
        state: dict,
        has_usable_image: bool,
        is_new_image: bool,
        image_quality: str,
    ) -> str:
        if not has_usable_image:
            return "request_image"
        if is_new_image and image_quality in ("too_small", "blurry"):
            return "request_clear_image"
        if state.get("summary_sent"):
            return "correction"
        return "extract_and_summarize"

    # ── Formatting helpers ────────────────────────────────────────────────────

    @staticmethod
    def _merge_description(existing: str, update: str) -> str:
        if not existing:
            return update.strip()
        return (existing + "\n" + update).strip()

    @staticmethod
    def _format_summary(attributes: dict[str, Any], language: str = "hinglish") -> str:
        materials = attributes.get("materials") or []
        if isinstance(materials, str):
            materials = [materials]
        dims = attributes.get("dimensions") or {}
        if isinstance(dims, dict):
            if any(dims.get(k) for k in ("length", "width", "height")):
                parts = [str(dims.get(k) or "") for k in ("length", "width", "height") if dims.get(k)]
                dim_str = "x".join(parts)
                if dims.get("unit"):
                    dim_str = f"{dim_str} {dims['unit']}"
            else:
                dim_str = dims.get("note") or dims.get("raw") or ""
        else:
            dim_str = str(dims) if dims else ""

        lines = [
            f"Naam: {attributes.get('name', '')}",
            f"Category: {attributes.get('category', '')}",
            f"Materials: {', '.join(materials)}",
            f"Dimensions: {dim_str}" if dim_str else "",
            f"Description: {attributes.get('description', '')}",
        ]
        header = "Maine yeh samjha:" if language != "english" else "Here are the product details:"
        summary = "\n".join(line for line in lines if line.strip())
        return f"{header}\n{summary}"

    @staticmethod
    def _build_summary_replies(
        reply: str, summary: str
    ) -> list[ConversationReply]:
        if not reply:
            return [ConversationReply(body=summary)]
        if "{SUMMARY}" in reply:
            return [ConversationReply(body=reply.replace("{SUMMARY}", summary))]
        return [ConversationReply(body=reply), ConversationReply(body=summary)]

    @staticmethod
    def _default_reply(phase: str) -> str:
        if phase == "request_clear_image":
            return (
                "Photo thodi blurry aa gayi 😊 Ek baar aur try karein — "
                "achhi roshni mein aur seedhi photo lein!"
            )
        return (
            "Hii! Banao mein aapka swagat hai 😊 "
            "Apne product ki ek achhi photo bhejiye, main details nikal dunga!"
        )

    @staticmethod
    def _is_user_confirming(text: str) -> bool:
        """Rule-based check for common confirmation phrases in Hindi/English/Hinglish."""
        if not text:
            return False
        t = text.lower().strip()
        patterns = [
            r"\b(haa|haan|ha)\b",
            r"\bsab\s*(sahi|shi|theek|ok|correct|acha|accha)\b",
            r"\bsahi\s*hai\b",
            r"\btheek\s*hai\b",
            r"\b(bilkul|perfect|done|confirm|confirmed)\b",
            r"^(ok|okay|k|yes|yeah|yep|yup|sure)\s*[!.]*$",
            r"\bno\s*change\b",
            r"\bkuch\s*nahi\b",
            r"\bsab\s*kuch\s*sahi\b",
        ]
        return any(re.search(p, t, re.IGNORECASE) for p in patterns)

    @staticmethod
    def _done_reply(language: str = "hinglish") -> str:
        if language == "english":
            return (
                "Thank you! We've noted your product details 😊 "
                "We'll get back to you soon!"
            )
        return (
            "Shukriya! Humne aapke product ki details note kar li hain 😊 "
            "Hum aapko jald hi contact karenge!"
        )

    @staticmethod
    def _normalize_quality(response_key: str) -> str:
        if response_key == "image_too_small":
            return "too_small"
        if response_key == "image_blurry":
            return "blurry"
        return "ok"
