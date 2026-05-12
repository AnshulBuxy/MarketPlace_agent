from __future__ import annotations

import time
from typing import Any

import httpx

from ...config import Settings
from .base import Listing, SearchQuery


class EbayConnector:
	"""eBay Browse API connector for active listings."""

	_TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
	_SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._access_token: str | None = None
		self._token_expires_at: float = 0.0

	async def search_listings(self, query: SearchQuery) -> list[Listing]:
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
