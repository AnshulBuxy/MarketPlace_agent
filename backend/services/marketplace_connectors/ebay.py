from __future__ import annotations

import time
from typing import Any

import httpx

from ...config import Settings
from .base import Listing, SearchQuery


class EbayConnector:
	"""eBay Browse API connector for active listings."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._access_token: str | None = None
		self._token_expires_at: float = 0.0
		
		# Determine environment based on client id prefix or explicit setting
		self.is_sandbox = (self._settings.ebay_client_id or "").startswith("AnshulBu-Banao-SBX-") or (self._settings.ebay_client_id or "").startswith("SBX-")
		self._base_domain = "api.sandbox.ebay.com" if self.is_sandbox else "api.ebay.com"
		
		self._TOKEN_URL = f"https://{self._base_domain}/identity/v1/oauth2/token"
		self._SEARCH_URL = f"https://{self._base_domain}/buy/browse/v1/item_summary/search"
		self._IMAGE_SEARCH_URL = f"https://{self._base_domain}/buy/browse/v1/item_summary/search_by_image"

	async def search_listings(self, query: SearchQuery) -> list[Listing]:
		if query.image_bytes:
			return await self._search_by_image(query)
		
		keywords = query.keywords.strip()
		if not keywords:
			return []
		access_token = await self._get_access_token()
		headers = {
			"Authorization": f"Bearer {access_token}",
			"X-EBAY-C-MARKETPLACE-ID": self._settings.ebay_marketplace_id,
		}
		params = {
			"q": keywords,
			"limit": query.limit,
		}
		async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
			response = await client.get(self._SEARCH_URL, params=params, headers=headers)
			response.raise_for_status()
			payload = response.json()
		items = payload.get("itemSummaries") or []
		listings: list[Listing] = []
		for item in items:
			listing = self._parse_listing(item)
			if listing:
				listings.append(listing)
		return listings

	async def _search_by_image(self, query: SearchQuery) -> list[Listing]:
		"""Search for items using an image."""
		import base64
		if not query.image_bytes:
			return []
		
		access_token = await self._get_access_token()
		headers = {
			"Authorization": f"Bearer {access_token}",
			"X-EBAY-C-MARKETPLACE-ID": self._settings.ebay_marketplace_id,
			"Content-Type": "application/json",
		}
		
		# eBay image search endpoint
		image_search_url = self._IMAGE_SEARCH_URL
		
		# Base64 encode image
		encoded_image = base64.b64encode(query.image_bytes).decode("utf-8")
		
		payload = {
			"image": encoded_image,
			"limit": query.limit,
		}
		
		async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
			response = await client.post(image_search_url, json=payload, headers=headers)
			if response.status_code != 200:
				logger.warning(f"eBay image search failed: {response.status_code} {response.text}")
				# Fallback to keyword search if available
				if query.keywords:
					return await self.search_listings(SearchQuery(keywords=query.keywords, limit=query.limit))
				return []
				
			payload = response.json()
			
		items = payload.get("itemSummaries") or []
		listings: list[Listing] = []
		for item in items:
			listing = self._parse_listing(item)
			if listing:
				listings.append(listing)
		return listings

	async def _get_access_token(self) -> str:
		if self._access_token and time.time() < self._token_expires_at - 60:
			return self._access_token
		if not self._settings.ebay_client_id or not self._settings.ebay_client_secret:
			raise ValueError("eBay API credentials are not configured")
		data = {
			"grant_type": "client_credentials",
			"scope": self._settings.ebay_oauth_scope,
		}
		auth = (self._settings.ebay_client_id, self._settings.ebay_client_secret)
		async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
			response = await client.post(self._TOKEN_URL, data=data, auth=auth)
			response.raise_for_status()
			payload = response.json()
		access_token = str(payload.get("access_token"))
		expires_in = float(payload.get("expires_in", 7200))
		self._access_token = access_token
		self._token_expires_at = time.time() + expires_in
		return access_token

	@staticmethod
	def _parse_listing(item: dict[str, Any]) -> Listing | None:
		price_data = item.get("price") or {}
		price_value = price_data.get("value")
		currency = price_data.get("currency")
		if price_value is None or not currency:
			return None
		try:
			price = float(price_value)
		except Exception:
			return None
		image_data = item.get("image") or {}
		shipping_price, shipping_currency = _extract_shipping(item)
		return Listing(
			title=str(item.get("title") or ""),
			price=price,
			currency=str(currency),
			url=str(item.get("itemWebUrl") or ""),
			image_url=str(image_data.get("imageUrl")) if image_data.get("imageUrl") else None,
			condition=str(item.get("condition") or "") or None,
			shipping_price=shipping_price,
			shipping_currency=shipping_currency,
			source="ebay",
			raw=item,
		)


def _extract_shipping(item: dict[str, Any]) -> tuple[float | None, str | None]:
	options = item.get("shippingOptions") or []
	if not options:
		return None, None
	first = options[0] or {}
	cost = first.get("shippingCost") or {}
	value = cost.get("value")
	currency = cost.get("currency")
	if value is None or not currency:
		return None, None
	try:
		return float(value), str(currency)
	except Exception:
		return None, None
