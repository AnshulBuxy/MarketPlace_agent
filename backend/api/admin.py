from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from uuid import UUID

from ..config import get_settings
from ..db import get_session
from ..models.product import Product
from ..models.artisan import Artisan
from ..services.whatsapp import send_twilio_whatsapp_message
from ..services.storage import StorageService
from ..services.image_generation import ImageGenerationService
from ..services.marketplace_pricing import find_marketplace_matches

router = APIRouter(prefix="/admin", tags=["admin"])


class WhatsAppSendRequest(BaseModel):
	"""Request body for a test WhatsApp send."""

	to_number: str = Field(..., examples=["whatsapp:+91xxxxxxxxxx"])
	body: str = Field(..., min_length=1)


@router.get("/ping")
def admin_ping() -> dict:
	"""Simple admin ping endpoint."""
	return {"status": "ok"}


@router.post("/whatsapp/send")
async def send_whatsapp_message(request: WhatsAppSendRequest) -> dict:
	"""Send a WhatsApp message through Twilio for testing."""
	settings = get_settings()
	try:
		result = await send_twilio_whatsapp_message(settings, request.to_number, request.body)
	except ValueError as exc:
		raise HTTPException(status_code=400, detail=str(exc)) from exc
	except Exception as exc:
		raise HTTPException(status_code=502, detail=f"Twilio send failed: {exc}") from exc
	return {
		"status": "sent",
		"message_sid": result.message_sid,
		"to_number": result.to_number,
		"from_number": result.from_number,
	}


@router.get("/submissions")
async def get_submissions(session: AsyncSession = Depends(get_session)) -> list[dict]:
	"""Get all live dynamic handcrafted submissions."""
	query = select(Product).options(joinedload(Product.artisan)).order_by(Product.created_at.desc())
	result = await session.execute(query)
	products = result.scalars().all()
	settings = get_settings()
	storage = StorageService(settings)
	
	submissions = []
	for p in products:
		art = p.artisan
		attrs = p.attributes or {}
		
		# Build confidence scores
		confidence_scores = [
			{"label": "Extraction", "value": p.extraction_confidence}
		]
		if "name" in attrs: confidence_scores.append({"label": "Category", "value": 0.95})
		if "materials" in attrs: confidence_scores.append({"label": "Materials", "value": 0.92})
		if "description" in attrs: confidence_scores.append({"label": "Description", "value": 0.91})
		
		dim = attrs.get("dimensions", "")
		if isinstance(dim, dict): dim = dim.get("raw", "")
		
		# Infer status
		if p.status:
			status = p.status.value.lower()
			if status == "ingested": status = "review" # Mapped for UI ease
		else:
			status = "review"

		thumbnail = "📦"
		img_src = p.image_url_enhanced or p.image_url
		if img_src:
			thumbnail = img_src
			if isinstance(thumbnail, str) and thumbnail.startswith("s3://"):
				try:
					thumbnail = storage.presign_s3_url(thumbnail)
				except Exception:
					pass

		media_urls = []
		if img_src: media_urls.append(img_src)
		media_urls.extend(attrs.get("ai_images", []))

		submissions.append({
			"id": str(p.id),
			"artisanId": str(art.id) if art else "unknown",
			"receivedAt": p.created_at.isoformat() if p.created_at else "",
			"status": status,
			"thumbnail": thumbnail,
			"voiceTranscript": p.transcript or "",
			"voiceLang": art.language if art and art.language else "Hindi",
			"craft": attrs.get("name") or "Handcrafted Item",
			"materials": attrs.get("materials") if isinstance(attrs.get("materials"), list) else [attrs.get("materials")] if attrs.get("materials") else [],
			"dimensions": dim,
			"description": attrs.get("description") or p.user_provided_description or "",
			"motifs": attrs.get("tags") or [],
			"confidence": p.extraction_confidence,
			"confidenceScores": confidence_scores,
			"expectedPrice": str(attrs.get("expected_price")) if attrs.get("expected_price") else "",
			"suggestedPrice": {"floor": 650, "mid": 950, "ceiling": 1300}, # mock suggestion
			"routedTo": [],
			"mediaUrls": media_urls,
			"drafts": [],
			"logs": [],
			"artisanInfo": {
				"name": art.name or "Artisan",
				"cluster": art.location or "Unknown Location",
				"phone": art.phone or "",
				"language": art.language or "Hindi"
			} if art else None
		})
	return submissions


@router.get("/submissions/{sub_id}")
async def get_submission(sub_id: str, session: AsyncSession = Depends(get_session)) -> dict:
	"""Get specific submission details."""
	try:
		product_uuid = UUID(sub_id)
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid submission UUID")
	
	query = select(Product).options(joinedload(Product.artisan)).where(Product.id == product_uuid)
	result = await session.execute(query)
	p = result.scalar_one_or_none()
	if not p:
		raise HTTPException(status_code=404, detail="Submission not found")
	
	settings = get_settings()
	storage = StorageService(settings)
	
	art = p.artisan
	attrs = p.attributes or {}

	confidence_scores = [
		{"label": "Extraction", "value": p.extraction_confidence}
	]
	if "name" in attrs: confidence_scores.append({"label": "Category", "value": 0.95})
	if "materials" in attrs: confidence_scores.append({"label": "Materials", "value": 0.92})
	if "description" in attrs: confidence_scores.append({"label": "Description", "value": 0.91})
	dim = attrs.get("dimensions", "")
	if isinstance(dim, dict): dim = dim.get("raw", "")
	
	status = p.status.value.lower() if p.status else "review"
	if status == "ingested": status = "review"

	thumbnail = "📦"
	img_src = p.image_url_enhanced or p.image_url
	if img_src:
		thumbnail = img_src
		if isinstance(thumbnail, str) and thumbnail.startswith("s3://"):
			try:
				thumbnail = storage.presign_s3_url(thumbnail)
			except Exception:
				pass

	img_src = p.image_url_enhanced or p.image_url
	media_urls = []
	if img_src:
		media_urls.append(img_src)
	ai_imgs = attrs.get("ai_images", [])
	media_urls.extend(ai_imgs)

	return {
		"id": str(p.id),
		"artisanId": str(art.id) if art else "unknown",
		"receivedAt": p.created_at.isoformat() if p.created_at else "",
		"status": status,
		"thumbnail": thumbnail,
		"voiceTranscript": p.transcript or "",
		"voiceLang": art.language if art and art.language else "Hindi",
		"craft": attrs.get("name") or "Handcrafted Item",
		"materials": attrs.get("materials") if isinstance(attrs.get("materials"), list) else [attrs.get("materials")] if attrs.get("materials") else [],
		"dimensions": dim,
		"description": attrs.get("description") or p.user_provided_description or "",
		"motifs": attrs.get("tags") or [],
		"confidence": p.extraction_confidence,
		"confidenceScores": confidence_scores,
		"expectedPrice": str(attrs.get("expected_price")) if attrs.get("expected_price") else "",
		"suggestedPrice": {"floor": 650, "mid": 950, "ceiling": 1300},
		"routedTo": [],
		"mediaUrls": media_urls,
		"drafts": [],
		"logs": [],
		"artisanInfo": {
			"name": art.name or "Artisan",
			"cluster": art.location or "Unknown Location",
			"phone": art.phone or "",
			"language": art.language or "Hindi"
		} if art else None
	}


@router.get("/submissions/{sub_id}/marketplace-pricing")
async def get_marketplace_pricing(sub_id: str, session: AsyncSession = Depends(get_session)) -> dict:
	"""Get four marketplace comparables from backend/agents/PriceData.json."""
	try:
		product_uuid = UUID(sub_id)
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid submission UUID")

	query = select(Product).where(Product.id == product_uuid)
	result = await session.execute(query)
	p = result.scalar_one_or_none()
	if not p:
		raise HTTPException(status_code=404, detail="Submission not found")

	attrs = p.attributes or {}
	product_name = attrs.get("name") or p.user_provided_description or "Product"
	description = attrs.get("description") or p.user_provided_description or ""
	matches = find_marketplace_matches(str(product_name), str(description), limit=4)
	return {
		"submissionId": str(p.id),
		"matches": matches,
	}

class GenerateCatalogRequest(BaseModel):
	styles: list[str] = Field(..., description="List of aesthetic styles to generate (e.g. 'studio_white', 'lifestyle')")

@router.post("/submissions/{sub_id}/generate-catalog")
async def generate_catalog_images(sub_id: str, payload: GenerateCatalogRequest, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_session)):
	"""Endpoint to trigger HF Image-to-Image agent for catalog generation."""
	try:
		product_uuid = UUID(sub_id)
	except ValueError:
		raise HTTPException(status_code=400, detail="Invalid submission UUID")
	
	query = select(Product).where(Product.id == product_uuid)
	result = await session.execute(query)
	p = result.scalar_one_or_none()
	if not p:
		raise HTTPException(status_code=404, detail="Submission not found")
	
	img_src = p.image_url_enhanced or p.image_url
	if not img_src:
		raise HTTPException(status_code=400, detail="Product has no original image to use as base.")

	settings = get_settings()
	storage = StorageService(settings)
	generator = ImageGenerationService(settings)

	# Fetch original image byte array
	try:
		orig_bytes = await storage.download_bytes_from_url(img_src)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Failed to fetch original image from storage: {str(e)}")

	generated_s3_paths = []

	# We generate one by one (this can be pushed to background task but we await for the dashboard UX)
	for style in payload.styles:
		# Build customized prompt 
		attrs = p.attributes or {}
		product_name = attrs.get("name", "handcrafted item")
		materials = attrs.get("materials", "natural materials")
		if isinstance(materials, list):
			materials = ", ".join(materials)

		if style == "studio_white":
			prompt = f"Professional studio photography of a {product_name} made of {materials}. Completely pure white background, soft lighting, hyper-realistic, high resolution catalog shot."
		elif style == "lifestyle":
			prompt = f"Beautiful lifestyle aesthetic photography of a {product_name} made of {materials}. Warm natural sunlight, placed on a modern wooden table, elegant background, Pinterest aesthetic."
		elif style == "close_up":
			prompt = f"Extreme macro detail shot of a {product_name} highlighting the fine {materials} texture. Shallow depth of field, sharp focus on craftsmanship."
		else:
			prompt = f"Professional product shot of {product_name}. High quality, photorealistic."

		# Call HF Model
		gen_bytes = await generator.generate_image_to_image(prompt, orig_bytes)

		# Upload to S3
		target_key = f"catalog/{sub_id}/{style}.jpg"
		new_s3_path = await storage.upload_bytes(target_key, gen_bytes, "image/jpeg")
		generated_s3_paths.append(new_s3_path)

	# Update Product AI Images
	new_attrs = dict(p.attributes) if p.attributes else {}
	ai_imgs = new_attrs.get("ai_images", [])
	
	for path in generated_s3_paths:
		if path not in ai_imgs:
			ai_imgs.append(path)
			
	new_attrs["ai_images"] = ai_imgs
	p.attributes = new_attrs
	
	await session.commit()

	# Presign all urls for immediate frontend use
	return_urls = []
	if img_src:
		return_urls.append(img_src)
	return_urls.extend(ai_imgs)

	presigned = []
	for url in return_urls:
		if isinstance(url, str) and url.startswith("s3://"):
			try:
				presigned.append(storage.presign_s3_url(url))
			except:
				presigned.append(url)
		else:
			presigned.append(url)

	return {"status": "success", "mediaUrls": presigned}

