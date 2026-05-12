from __future__ import annotations

import io
import math
from statistics import mean
from dataclasses import dataclass
from uuid import UUID, uuid4

from PIL import Image, ImageEnhance, ImageFilter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models.artisan import Artisan
from ..models.enums import MessageType, ProductStatus
from ..models.inbound_message import InboundMessage
from ..models.product import Product
from ..services.speech import SpeechService
from ..services.storage import StorageService
from ..services.whatsapp import TwilioInboundMessage
from ..utils.audit import log_event
from ..utils.http import fetch_bytes

import logging

logger = logging.getLogger(__name__)


@dataclass
class IngestionResult:
	"""Result of ingestion processing."""

	response_key: str
	message_type: MessageType
	product_id: UUID | None


async def _get_or_create_artisan(session: AsyncSession, phone: str) -> Artisan:
	"""Find an artisan by phone or create a stub profile."""
	result = await session.execute(select(Artisan).where(Artisan.phone == phone))
	artisan = result.scalar_one_or_none()
	if artisan:
		return artisan
	artisan = Artisan(phone=phone)
	session.add(artisan)
	await session.flush()
	return artisan


def _is_image_clear(image_bytes: bytes, min_px: int) -> bool:
	"""Return True if the image meets minimum size requirements."""
	try:
		with Image.open(io.BytesIO(image_bytes)) as img:
			width, height = img.size
		return width >= min_px and height >= min_px
	except Exception:
		return False


def _blur_variance(image_bytes: bytes) -> float:
	"""Compute a blur score using edge variance; lower means blurrier."""
	try:
		with Image.open(io.BytesIO(image_bytes)) as img:
			gray = img.convert("L")
			edges = gray.filter(ImageFilter.FIND_EDGES)
			pixels = list(edges.getdata())
			if not pixels:
				return 0.0
			avg = mean(pixels)
			variance = mean([(p - avg) ** 2 for p in pixels])
			return float(variance)
	except Exception:
		return 0.0


def _enhance_image(image_bytes: bytes) -> bytes:
	"""Apply a lightweight enhancement using PIL filters."""
	with Image.open(io.BytesIO(image_bytes)) as img:
		image = img.convert("RGB")
		enhanced = image.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
		enhanced = ImageEnhance.Contrast(enhanced).enhance(1.2)
		enhanced = ImageEnhance.Sharpness(enhanced).enhance(1.3)
		output = io.BytesIO()
		enhanced.save(output, format="JPEG", quality=92)
		return output.getvalue()


async def ingest_twilio_message(
	payload: TwilioInboundMessage,
	session: AsyncSession,
	settings: Settings,
) -> IngestionResult:
	"""Ingest a Twilio WhatsApp message into storage and DB."""
	artisan = await _get_or_create_artisan(session, payload.from_number)

	message_type = MessageType.TEXT if payload.body else MessageType.OTHER
	if any(media.is_image() for media in payload.media):
		message_type = MessageType.IMAGE
	elif any(media.is_audio() for media in payload.media):
		message_type = MessageType.AUDIO

	inbound = InboundMessage(
		message_sid=payload.message_sid,
		from_number=payload.from_number,
		message_type=message_type,
		num_media=len(payload.media),
		media_urls=[{"url": media.url, "content_type": media.content_type} for media in payload.media],
		payload=payload.raw_payload,
		artisan_id=artisan.id,
	)
	session.add(inbound)
	await session.flush()

	response_key = "acknowledgement"
	product: Product | None = None
	image_quality_ok = True

	if payload.media:
		logger.info(
			"Ingestion: media received from=%s count=%s",
			payload.from_number,
			len(payload.media),
		)
		product = Product(
			id=uuid4(),
			artisan_id=artisan.id,
			source_message_id=inbound.id,
			status=ProductStatus.INGESTED,
			image_quality_ok=True,
		)
		session.add(product)
		await session.flush()
		logger.info("Ingestion: product created id=%s", product.id)

		storage = StorageService(settings)
		auth = None
		if settings.twilio_account_sid and settings.twilio_auth_token:
			auth = (settings.twilio_account_sid, settings.twilio_auth_token)

		for media in payload.media:
			if media.is_image() and product.image_url is None:
				logger.info("Ingestion: downloading image url=%s", media.url)
				image_bytes = await fetch_bytes(
					media.url,
					auth=auth,
					timeout_seconds=settings.http_timeout_seconds,
					max_retries=settings.http_max_retries,
				)
				image_quality_ok = _is_image_clear(image_bytes, settings.min_image_px)
				blur_variance = _blur_variance(image_bytes)
				is_blurry = blur_variance < settings.min_blur_variance
				logger.info(
					"Ingestion: image quality ok=%s min_px=%s blur_variance=%.2f threshold=%.2f",
					image_quality_ok,
					settings.min_image_px,
					blur_variance,
					settings.min_blur_variance,
				)
				if not image_quality_ok:
					response_key = "image_too_small"
				elif is_blurry:
					response_key = "image_blurry"
				ext = media.content_type.split("/")[-1]
				key = f"products/{product.id}/image.{ext}"
				product.image_url = await storage.upload_bytes(key, image_bytes, media.content_type)
				product.image_quality_ok = image_quality_ok and not is_blurry
				logger.info("Ingestion: image uploaded key=%s", key)

				# Enhance image and store
				enhanced_bytes = _enhance_image(image_bytes)
				enhanced_key = f"products/{product.id}/image_enhanced.jpg"
				product.image_url_enhanced = await storage.upload_bytes(
					enhanced_key,
					enhanced_bytes,
					"image/jpeg",
				)
				logger.info("Ingestion: enhanced image uploaded key=%s", enhanced_key)
				# Store blur score in payload for orchestrator
				product.attributes = product.attributes or {}
				product.attributes["blur_variance"] = blur_variance
				product.attributes["is_blurry"] = is_blurry

			if media.is_audio() and product.audio_url is None:
				logger.info("Ingestion: downloading audio url=%s", media.url)
				audio_bytes = await fetch_bytes(
					media.url,
					auth=auth,
					timeout_seconds=settings.http_timeout_seconds,
					max_retries=settings.http_max_retries,
				)
				ext = media.content_type.split("/")[-1]
				key = f"products/{product.id}/audio.{ext}"
				product.audio_url = await storage.upload_bytes(key, audio_bytes, media.content_type)
				logger.info("Ingestion: audio uploaded key=%s", key)

				speech = SpeechService(settings)
				transcript = await speech.transcribe_audio(
					audio_bytes,
					filename=f"audio.{ext}",
					content_type=media.content_type,
				)
				product.transcript = transcript
				if response_key == "acknowledgement":
					response_key = "voice_received"

	await log_event(
		session=session,
		agent="ingestion",
		action="ingest_twilio_message",
		input_data={
			"from_number": payload.from_number,
			"message_type": message_type.value,
			"num_media": len(payload.media),
		},
		output_data={
			"product_id": str(product.id) if product else None,
			"image_quality_ok": image_quality_ok,
			"blur_variance": product.attributes.get("blur_variance") if product and product.attributes else None,
			"is_blurry": product.attributes.get("is_blurry") if product and product.attributes else None,
			"response_key": response_key,
		},
		product_id=product.id if product else None,
	)

	return IngestionResult(
		response_key=response_key,
		message_type=message_type,
		product_id=product.id if product else None,
	)


async def process_ingestion_message(
	message_data: dict,
	session: AsyncSession,
	settings: Settings,
) -> dict:
	"""
	Process ingestion message for orchestrator node.
	
	Returns dict with:
	- success: bool
	- product_id: str
	- image_quality_ok: bool
	- media_url: Optional[str]
	- transcription: Optional[str]
	- error: Optional[str]
	"""
	try:
		from ..services.whatsapp import parse_twilio_payload
		
		# Parse message
		payload = parse_twilio_payload(message_data)
		
		# Ingest using existing logic
		result = await ingest_twilio_message(payload, session, settings)
		
		await session.commit()
		
		# Get product details for output
		if result.product_id:
			product = await session.get(Product, result.product_id)
			return {
				"success": True,
				"product_id": str(result.product_id),
				"image_quality_ok": result.response_key != "image_too_small",
				"media_url": product.image_url or product.audio_url if product else None,
				"enhanced_media_url": product.image_url_enhanced if product else None,
				"is_blurry": product.attributes.get("is_blurry") if product and product.attributes else None,
				"blur_variance": product.attributes.get("blur_variance") if product and product.attributes else None,
				"transcription": product.transcript if product else None,
			}
		else:
			return {
				"success": True,
				"product_id": None,
				"image_quality_ok": False,
				"media_url": None,
				"transcription": None,
			}
	
	except Exception as e:
		await session.rollback()
		return {
			"success": False,
			"error": str(e),
		}
