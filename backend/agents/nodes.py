"""
Agent Nodes - Implementation of specific agent tasks.

Includes:
- IngestionNode: Process WhatsApp message, download media, create product
- ExtractionNode: Extract product attributes using vision LLM
"""

from __future__ import annotations

import logging
import mimetypes
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models.product import Product
from ..services.llm import GeminiService
from ..services.storage import StorageService
from ..orchestrator import (
	AgentNodeContract,
	AgentNodeInput,
	AgentNodeOutput,
	NodeType,
)
from ..utils.audit import log_event

logger = logging.getLogger(__name__)


class IngestionNode(AgentNodeContract):
	"""
	Ingestion Agent Node.
	
	Handles:
	- Parse WhatsApp message from Twilio
	- Download media if present
	- Store to S3
	- Create Product record
	- Check image quality
	"""
	
	def __init__(self):
		super().__init__(NodeType.INGESTION)
	
	async def execute(self, node_input: AgentNodeInput) -> AgentNodeOutput:
		"""
		Execute ingestion workflow.
		
		Returns next node: EXTRACTION (if product created)
		Triggers human gate for description collection if image found.
		"""
		state = node_input.workflow_state
		session = node_input.session
		settings = node_input.settings
		
		try:
			from .ingestion import process_ingestion_message
			
			def _first(value: object) -> str:
				if isinstance(value, list):
					return str(value[0]) if value else ""
				return str(value or "")
			
			# Get ingestion message - should be in node_outputs from previous iteration
			if "ingestion_message" not in state.node_outputs and state.inbound_message_id:
				# Fetch from DB
				from ..models.inbound_message import InboundMessage
				msg = await session.get(InboundMessage, state.inbound_message_id)
				if not msg:
					return AgentNodeOutput(
						success=False,
						error="Inbound message not found"
					)
				message_data = {
					"From": msg.from_number,
					"Body": msg.body,
					"NumMedia": msg.num_media,
				}
			else:
				message_data = state.node_outputs.get("ingestion_message")
			
			contact_number = _first(message_data.get("From")) if message_data else ""
			
			if not message_data:
				return AgentNodeOutput(
					success=False,
					error="No ingestion message provided"
				)
			logger.info(
				"IngestionNode: from=%s has_media=%s",
				contact_number,
				bool(message_data.get("NumMedia")),
			)
			
			# Process message
			result = await process_ingestion_message(
				message_data,
				session,
				settings
			)
			
			if not result.get("success"):
				logger.error("IngestionNode failed: %s", result.get("error"))
				return AgentNodeOutput(
					success=False,
					error=result.get("error", "Ingestion failed")
				)
			
			# Extract outputs
			product_id = result.get("product_id")
			image_quality_ok = result.get("image_quality_ok", True)
			media_url = result.get("media_url")
			enhanced_media_url = result.get("enhanced_media_url")
			is_blurry = result.get("is_blurry")
			transcription = result.get("transcription")
			has_image = media_url is not None
			
			# If poor image quality, ask for better photo
			if not image_quality_ok:
				logger.info("IngestionNode: image quality too low, asking for new photo")
				return AgentNodeOutput(
					success=True,
					next_node=NodeType.EXTRACTION,
					node_outputs={
						"product_id": product_id,
						"image_quality_ok": image_quality_ok,
						"media_url": media_url,
						"transcription": transcription,
						"contact_number": contact_number,
					},
					confidence_scores={
						"ingestion": 1.0,
					},
					human_gate_question="Your photo is too small or unclear. Please send a clearer, larger photo.",
				)
			
			# If image is blurry, send enhanced preview and ask for retry/continue
			if has_image and is_blurry:
				return AgentNodeOutput(
					success=True,
					next_node=NodeType.EXTRACTION,
					node_outputs={
						"product_id": product_id,
						"image_quality_ok": image_quality_ok,
						"media_url": media_url,
						"enhanced_media_url": enhanced_media_url,
						"transcription": transcription,
						"contact_number": contact_number,
						"is_blurry": is_blurry,
					},
					confidence_scores={
						"ingestion": 1.0,
					},
					human_gate_question="Your image looks blurry. I enhanced it and sent a preview. Can I proceed with this, or will you send another image? Reply 'proceed' to continue or send a new image.",
				)

			# If we have an image, ask for description to improve extraction
			if has_image:
				logger.info("IngestionNode: image detected, requesting description")
				return AgentNodeOutput(
					success=True,
					next_node=NodeType.EXTRACTION,
					node_outputs={
						"product_id": product_id,
						"image_quality_ok": image_quality_ok,
						"media_url": media_url,
						"enhanced_media_url": enhanced_media_url,
						"transcription": transcription,
						"contact_number": contact_number,
					},
					confidence_scores={
						"ingestion": 1.0,
					},
					human_gate_question="Great! Now please describe this product. What material is it? What are its dimensions? Any special features? (Or reply 'skip' to skip description)",
				)
			
			# No image, just proceed to extraction with text
			return AgentNodeOutput(
				success=True,
				next_node=NodeType.EXTRACTION,
				node_outputs={
					"product_id": product_id,
					"image_quality_ok": image_quality_ok,
					"media_url": media_url,
					"transcription": transcription,
					"contact_number": contact_number,
				},
				confidence_scores={
					"ingestion": 1.0,
				},
			)
		
		except Exception as e:
			logger.error(f"IngestionNode error: {str(e)}")
			return AgentNodeOutput(
				success=False,
				error=str(e)
			)


class ExtractionNode(AgentNodeContract):
	"""
	Extraction Agent Node - Phase 1 Stub.
	
	Extracts product attributes from image and text using vision LLM.
	
	Handles:
	- Call vision LLM (Gemini) with image + description
	- Parse structured attributes
	- Assign confidence scores
	- Trigger human gate if low confidence
	"""
	
	def __init__(self):
		super().__init__(NodeType.EXTRACTION)
	
	async def execute(self, node_input: AgentNodeInput) -> AgentNodeOutput:
		"""
		Execute extraction workflow.
		
		Uses image + artisan-provided description for better results.
		For Phase 1: Return stub with high confidence.
		Phase 2 will integrate real Gemini vision.
		"""
		state = node_input.workflow_state
		session = node_input.session
		settings = node_input.settings
		
		try:
			# Get ingestion outputs
			ingestion_outputs = state.node_outputs.get("ingestion", {})
			product_id = ingestion_outputs.get("product_id")
			media_url = ingestion_outputs.get("media_url")
			transcription = ingestion_outputs.get("transcription", "")
			logger.info(
				"ExtractionNode: product_id=%s has_image=%s has_description=%s",
				product_id,
				bool(media_url),
				bool(state.human_gate_response),
			)
			
			# Get description provided by artisan via human gate response
			user_description = state.human_gate_response or ""
			skip_description = user_description.lower().strip() == "skip"
			
			if skip_description:
				user_description = ""
			
			if not product_id:
				# Try from state directly as fallback
				product_id = state.product_id
			
			if not product_id:
				return AgentNodeOutput(
					success=False,
					error="Product ID not found"
				)
			
			attributes: dict[str, Any]
			confidence_scores: dict[str, float]
			
			if media_url and settings.google_api_key:
				try:
					storage = StorageService(settings)
					image_bytes = await storage.download_bytes_from_url(media_url)
					mime_type = mimetypes.guess_type(media_url)[0] or "image/jpeg"
					gemini = GeminiService(settings)
					attributes, confidence_scores = await gemini.extract_attributes(
						image_bytes=image_bytes,
						mime_type=mime_type,
						user_description=user_description,
						transcription=transcription,
					)
					logger.info("ExtractionNode: Gemini multimodal extraction completed")
					if not confidence_scores:
						confidence_scores = {
							"name": 0.7,
							"category": 0.7,
							"materials": 0.6,
							"dimensions": 0.6,
							"description": 0.7,
						}
				except Exception as exc:
					logger.error("ExtractionNode: Gemini failed, fallback to heuristic. error=%s", exc)
					attributes = {
						"name": user_description.split("\n")[0][:50] if user_description else "Handcrafted Product",
						"category": "Handcraft",
						"materials": self._extract_materials(user_description),
						"dimensions": self._extract_dimensions(user_description),
						"description": user_description or "Beautiful handcrafted item",
						"tags": self._extract_tags(user_description),
						"info_source": "fallback_heuristic",
					}
					attributes_given = bool(user_description)
					confidence_scores = {
						"name": 0.9 if attributes_given else 0.7,
						"category": 0.85,
						"materials": 0.8 if attributes_given else 0.6,
						"dimensions": 0.85 if attributes_given else 0.5,
						"description": 0.95 if attributes_given else 0.5,
					}
			else:
				attributes = {
					"name": user_description.split("\n")[0][:50] if user_description else "Handcrafted Product",
					"category": "Handcraft",
					"materials": self._extract_materials(user_description),
					"dimensions": self._extract_dimensions(user_description),
					"description": user_description or "Beautiful handcrafted item",
					"tags": self._extract_tags(user_description),
					"info_source": "no_image_or_no_key",
				}
				attributes_given = bool(user_description)
				confidence_scores = {
					"name": 0.9 if attributes_given else 0.7,
					"category": 0.85,
					"materials": 0.8 if attributes_given else 0.6,
					"dimensions": 0.85 if attributes_given else 0.5,
					"description": 0.95 if attributes_given else 0.5,
				}
			
			# Update product with attributes
			from ..models.product import Product
			product = await session.get(Product, product_id)
			if product:
				product.attributes = attributes
				product.extraction_confidence = sum(confidence_scores.values()) / len(confidence_scores)
				product.user_provided_description = user_description
				await session.flush()
				logger.info(
					"ExtractionNode: attributes saved product_id=%s confidence=%.2f",
					product_id,
					product.extraction_confidence,
				)
				await log_event(
					session=session,
					agent="extraction",
					action="extract_attributes",
					input_data={
						"product_id": str(product_id),
						"media_url": media_url,
						"user_description": user_description,
						"transcription": transcription,
					},
					output_data={
						"attributes": attributes,
						"confidence_scores": confidence_scores,
					},
					product_id=product.id,
				)
			
			return AgentNodeOutput(
				success=True,
				next_node=NodeType.MARKETPLACE_ROUTING,
				node_outputs=attributes,
				confidence_scores=confidence_scores,
				human_gate_question="Please confirm/correct these attributes for better marketplace matching. Materials and dimensions are especially important." if min(confidence_scores.values()) < 0.7 else None,
			)
		
		except Exception as e:
			logger.error(f"ExtractionNode error: {str(e)}")
			return AgentNodeOutput(
				success=False,
				error=str(e)
			)
	
	def _extract_materials(self, description: str) -> list[str]:
		"""Extract material mentions from description."""
		if not description:
			return ["Natural materials"]
		
		materials_keywords = {
			"cotton": ["cotton", "कपास"],
			"silk": ["silk", "रेशम"],
			"wool": ["wool", "ऊन"],
			"linen": ["linen", "सन"],
			"hemp": ["hemp", "भांग"],
			"jute": ["jute", "जूट"],
			"paper": ["paper", "कागज"],
			"clay": ["clay", "मिट्टी"],
			"wood": ["wood", "लकड़ी"],
			"metal": ["metal", "धातु", "iron", "copper", "brass"],
			"ceramic": ["ceramic", "陶瓷"],
		}
		
		found_materials = []
		desc_lower = description.lower()
		for material, keywords in materials_keywords.items():
			if any(kw in desc_lower for kw in keywords):
				found_materials.append(material.title())
		
		return found_materials if found_materials else ["Handcrafted material"]
	
	def _extract_dimensions(self, description: str) -> dict:
		"""Extract dimension mentions from description."""
		if not description:
			return {"note": "Dimensions not specified"}
		
		import re
		# Look for patterns like "30cm", "30 cm", "30 inches", etc
		dim_pattern = r"(\d+(?:\.\d+)?)\s*(?:cm|inch|inches|mm|meters?)"
		matches = re.findall(dim_pattern, description, re.IGNORECASE)
		
		if matches:
			return {
				"raw": description,
				"found_measurements": matches,
			}
		
		return {"raw": description}
	
	def _extract_tags(self, description: str) -> list[str]:
		"""Extract relevant tags from description."""
		default_tags = ["handmade", "artisan"]
		
		if not description:
			return default_tags
		
		tag_keywords = {
			"unique": ["unique", "one-of-a-kind", "custom"],
			"eco-friendly": ["eco", "sustainable", "organic", "natural"],
			"vintage": ["vintage", "old", "traditional", "antique"],
			"modern": ["modern", "contemporary", "design"],
			"colorful": ["colorful", "colors", "vibrant"],
		}
		
		desc_lower = description.lower()
		tags = default_tags.copy()
		
		for tag, keywords in tag_keywords.items():
			if any(kw in desc_lower for kw in keywords):
				tags.append(tag)
		
		return list(set(tags))  # Remove duplicates


class MarketplaceRoutingNode(AgentNodeContract):
	"""
	Marketplace Routing Agent Node - Phase 1 Stub.
	
	Routes product to best marketplace(s).
	"""
	
	def __init__(self):
		super().__init__(NodeType.MARKETPLACE_ROUTING)
	
	async def execute(self, node_input: AgentNodeInput) -> AgentNodeOutput:
		"""Route to marketplace."""
		try:
			# Phase 1: Stub - route to default marketplace
			product_id = node_input.workflow_state.product_id
			if not product_id:
				product_id = node_input.workflow_state.node_outputs.get("ingestion", {}).get("product_id")
			product_uuid = None
			if product_id:
				from ..models.product import Product
				product = await node_input.session.get(Product, product_id)
				if product:
					product_uuid = product.id
			logger.info(
				"MarketplaceRoutingNode: product_id=%s routing=shopify",
				product_id,
			)
			await log_event(
				session=node_input.session,
				agent="marketplace_routing",
				action="route_marketplace",
				input_data={
					"product_id": product_id,
					"attributes": node_input.workflow_state.node_outputs.get("extraction", {}),
				},
				output_data={
					"marketplace": "shopify",
					"reason": "Default marketplace for Phase 1",
				},
				product_id=product_uuid,
			)
			return AgentNodeOutput(
				success=True,
				next_node=NodeType.PRICING,
				node_outputs={
					"marketplace": "shopify",
					"reason": "Default marketplace for Phase 1",
				},
				confidence_scores={
					"marketplace_selection": 0.8,
				}
			)
		except Exception as e:
			logger.error(f"MarketplaceRoutingNode error: {str(e)}")
			return AgentNodeOutput(
				success=False,
				error=str(e)
			)
