from __future__ import annotations

import logging
from typing import Any

import httpx

from ...config import Settings
from .base import Listing, SearchQuery

logger = logging.getLogger(__name__)

class GoogleShoppingConnector:
	"""Google Shopping connector via SerpApi for precise regional price monitoring."""

	_API_URL = "https://serpapi.com/search"

	def __init__(self, settings: Settings) -> None:
		self._settings = settings

	async def search_listings(self, query: SearchQuery) -> list[Listing]:
		"""Search for products on Google Shopping with Indian regional filters."""
		if not self._settings.serpapi_api_key:
			logger.warning("SerpApi API key not configured. Skipping Google Shopping search.")
			return []

		params: dict[str, Any] = {
			"engine": "google_shopping",
			"q": query.keywords,
			"api_key": self._settings.serpapi_api_key,
			"gl": self._settings.google_lens_gl, # Reusing 'in'
			"hl": self._settings.google_lens_hl, # Reusing 'en'
			"google_domain": "google.co.in" if self._settings.google_lens_gl == "in" else "google.com",
			"num": query.limit,
		}

		try:
			async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
				response = await client.get(self._API_URL, params=params)
				response.raise_for_status()
				payload = response.json()
			
			shopping_results = payload.get("shopping_results") or []
			
			listings: list[Listing] = []
			for item in shopping_results:
				listing = self._parse_listing(item)
				if listing:
					listings.append(listing)
			
			logger.info(f"GoogleShoppingConnector: Found {len(listings)} results for '{query.keywords}' in {params['gl']}")
			return listings

		except Exception as e:
			logger.error(f"GoogleShoppingConnector: Search failed: {e}")
			return []

	@staticmethod
	def _parse_listing(item: dict[str, Any]) -> Listing | None:
		"""Parse a SerpApi Google Shopping result into a standard Listing."""
		title = item.get("title")
		link = item.get("link")
		source = item.get("source")
		
		# Price handling
		price = item.get("extracted_price")
		currency = "INR" if "₹" in (item.get("price") or "") else "USD"
		
		# SerpApi shopping results often provide currency explicitly too if available
			
		if not title or not link or price is None:
			return None
			
		return Listing(
			title=str(title),
			price=float(price),
			currency=currency,
			url=str(link),
			image_url=str(item.get("thumbnail")),
			condition=None,
			shipping_price=None,
			shipping_currency=None,
			source=str(source or "google_shopping"),
			raw=item,
		)
