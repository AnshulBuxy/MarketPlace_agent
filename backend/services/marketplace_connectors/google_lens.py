from __future__ import annotations

import logging
from typing import Any

import httpx

from ...config import Settings
from .base import Listing, SearchQuery

logger = logging.getLogger(__name__)

class GoogleLensConnector:
	"""Google Lens connector via SerpApi for visual product matching."""

	_API_URL = "https://serpapi.com/search"

	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	async def search_listings(self, query: SearchQuery) -> list[Listing]:
		"""
		Search for products using Google Lens via SerpApi.
		Note: SerpApi requires a publicly accessible image URL.
		"""
		if not self._settings.serpapi_api_key:
			logger.warning("SerpApi API key not configured. Skipping Google Lens search.")
			return []

		if not query.image_url:
			if query.image_bytes:
				logger.warning("GoogleLensConnector: SerpApi requires a public URL. Binary uploads are not supported for Visual Search.")
			logger.info("GoogleLensConnector: No image_url provided, skipping visual search.")
			return []

		params: dict[str, Any] = {
			"engine": "google_lens",
			"url": query.image_url,
			"api_key": self._settings.serpapi_api_key,
			"gl": self._settings.google_lens_gl,
			"hl": self._settings.google_lens_hl,
			"limit": query.limit,
		}

		if self._settings.google_lens_gl == "in":
			params["google_domain"] = "google.co.in"

		try:
			async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
				response = await client.get(self._API_URL, params=params)
				response.raise_for_status()
				payload = response.json()
			
			# SerpApi Google Lens results are usually in 'visual_matches' or 'knowledge_graph'
			# For shopping, it specifically has a 'visual_matches' section
			matches = payload.get("visual_matches") or []
			
			listings: list[Listing] = []
			for item in matches:
				listing = self._parse_listing(item)
				if listing:
					listings.append(listing)
			
			logger.info(f"GoogleLensConnector: Found {len(listings)} matches for {query.image_url}")
			return listings

		except Exception as e:
			logger.error(f"GoogleLensConnector: Search failed: {e}")
			return []

	@staticmethod
	def _parse_listing(item: dict[str, Any]) -> Listing | None:
		"""Parse a SerpApi visual match into a standard Listing."""
		title = item.get("title")
		link = item.get("link")
		
		# Prices in SerpApi are often in 'price' object or as a string in 'price'
		price_data = item.get("price") or {}
		
		# Sometimes price is a string like "$29.99"
		raw_price = None
		currency = "USD"
		
		if isinstance(price_data, dict):
			raw_price = price_data.get("extracted_value")
			currency = price_data.get("currency") or "USD"
		elif isinstance(price_data, str):
			# Simple regex extraction could go here, but SerpApi usually provides extracted_value
			pass
			
		if not title or not link or raw_price is None:
			return None
			
		return Listing(
			title=str(title),
			price=float(raw_price),
			currency=str(currency),
			url=str(link),
			image_url=str(item.get("thumbnail")),
			condition=None,
			shipping_price=None,
			shipping_currency=None,
			source=str(item.get("source", "google_lens")),
			raw=item,
		)
