from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

import httpx

from ..config import Settings
from .marketplace_connectors.base import Listing, SearchQuery
from .marketplace_connectors.ebay import EbayConnector


@dataclass
class PriceRequest:
	image_url: str | None
	description: str
	attributes: dict[str, Any]


@dataclass
class ListingPrice:
	title: str
	url: str
	price: float
	currency: str
	price_inr: float
	shipping_price: float | None
	shipping_inr: float | None
	source: str
	match_score: float


@dataclass
class PriceResponse:
	suggested_price_inr: float
	min_price_inr: float
	max_price_inr: float
	currency: str
	confidence: float
	matches: list[ListingPrice]


class FxRateService:
	"""Fetches FX rates with caching."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._cache: dict[tuple[str, str], float] = {}

	async def get_rate(self, base_currency: str, target_currency: str) -> float:
		base = base_currency.upper()
		target = target_currency.upper()
		if base == target:
			return 1.0
		cache_key = (base, target)
		if cache_key in self._cache:
			return self._cache[cache_key]

		rate = await self._fetch_rate(base, target)
		self._cache[cache_key] = rate
		return rate

	async def _fetch_rate(self, base: str, target: str) -> float:
		if self._settings.fx_rate_base_url:
			params = {"base": base, "symbols": target}
			try:
				async with httpx.AsyncClient(timeout=self._settings.http_timeout_seconds) as client:
					response = await client.get(self._settings.fx_rate_base_url, params=params)
					response.raise_for_status()
					payload = response.json()
					rate = float((payload.get("rates") or {}).get(target))
					if rate > 0:
						return rate
			except Exception:
				pass

		if base == "USD" and target == "INR" and self._settings.fx_rate_inr_per_usd:
			return float(self._settings.fx_rate_inr_per_usd)

		raise ValueError("FX rate unavailable. Configure FX_RATE_INR_PER_USD or FX_RATE_BASE_URL")


class PricingAgent:
	"""Standalone pricing agent using eBay listings."""

	def __init__(self, settings: Settings) -> None:
		self._settings = settings
		self._connector = EbayConnector(settings)
		self._fx = FxRateService(settings)

	async def run(self, request: PriceRequest, limit: int = 20, top_n: int = 5) -> PriceResponse:
		keywords = self._build_keywords(request.description, request.attributes)
		query = SearchQuery(keywords=keywords, limit=limit)
		listings = await self._connector.search_listings(query)
		if not listings:
			return PriceResponse(
				suggested_price_inr=0.0,
				min_price_inr=0.0,
				max_price_inr=0.0,
				currency="INR",
				confidence=0.0,
				matches=[],
			)

		tokens = self._tokenize(keywords)
		priced_matches: list[ListingPrice] = []
		prices_inr: list[float] = []
		for listing in listings:
			price_inr, shipping_inr = await self._convert_listing_to_inr(listing)
			if price_inr <= 0:
				continue
			total_inr = price_inr + (shipping_inr or 0.0)
			match_score = self._score_listing(listing, tokens)
			prices_inr.append(total_inr)
			priced_matches.append(
				ListingPrice(
					title=listing.title,
					url=listing.url,
					price=listing.price,
					currency=listing.currency,
					price_inr=total_inr,
					shipping_price=listing.shipping_price,
					shipping_inr=shipping_inr,
					source=listing.source,
					match_score=match_score,
				)
			)

		filtered = self._filter_outliers(prices_inr)
		suggested = self._median(filtered)
		min_price = self._percentile(filtered, 0.25)
		max_price = self._percentile(filtered, 0.75)
		confidence = min(1.0, len(filtered) / max(1.0, float(limit)))

		priced_matches.sort(key=lambda item: (-item.match_score, item.price_inr))
		return PriceResponse(
			suggested_price_inr=round(suggested, 2),
			min_price_inr=round(min_price, 2),
			max_price_inr=round(max_price, 2),
			currency="INR",
			confidence=round(confidence, 2),
			matches=priced_matches[:top_n],
		)

	async def _convert_listing_to_inr(self, listing: Listing) -> tuple[float, float | None]:
		rate = await self._fx.get_rate(listing.currency, "INR")
		price_inr = listing.price * rate
		shipping_inr = None
		if listing.shipping_price is not None and listing.shipping_currency:
			shipping_rate = await self._fx.get_rate(listing.shipping_currency, "INR")
			shipping_inr = listing.shipping_price * shipping_rate
		return price_inr, shipping_inr

	@staticmethod
	def _build_keywords(description: str, attributes: dict[str, Any]) -> str:
		pieces: list[str] = []
		for key in ("name", "category"):
			value = attributes.get(key)
			if isinstance(value, str) and value.strip():
				pieces.append(value.strip())
		materials = attributes.get("materials") or []
		if isinstance(materials, str):
			materials = [materials]
		pieces.extend([str(item).strip() for item in materials if str(item).strip()])
		tags = attributes.get("tags") or []
		if isinstance(tags, str):
			tags = [tags]
		pieces.extend([str(item).strip() for item in tags if str(item).strip()])
		if description:
			pieces.append(description.strip())
		clean = " ".join(pieces)
		return " ".join(clean.split())

	@staticmethod
	def _tokenize(text: str) -> set[str]:
		tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
		return set(tokens)

	def _score_listing(self, listing: Listing, tokens: set[str]) -> float:
		if not tokens:
			return 0.0
		title_tokens = self._tokenize(listing.title)
		return len(tokens & title_tokens) / float(len(tokens))

	@staticmethod
	def _filter_outliers(values: list[float]) -> list[float]:
		if len(values) < 4:
			return values
		ordered = sorted(values)
		q1 = PricingAgent._percentile(ordered, 0.25)
		q3 = PricingAgent._percentile(ordered, 0.75)
		iqr = q3 - q1
		low = q1 - 1.5 * iqr
		high = q3 + 1.5 * iqr
		return [value for value in values if low <= value <= high]

	@staticmethod
	def _median(values: list[float]) -> float:
		if not values:
			return 0.0
		ordered = sorted(values)
		mid = len(ordered) // 2
		if len(ordered) % 2 == 0:
			return (ordered[mid - 1] + ordered[mid]) / 2
		return ordered[mid]

	@staticmethod
	def _percentile(values: list[float], percentile: float) -> float:
		if not values:
			return 0.0
		ordered = sorted(values)
		if len(ordered) == 1:
			return ordered[0]
		k = (len(ordered) - 1) * percentile
		f = math.floor(k)
		c = math.ceil(k)
		if f == c:
			return ordered[int(k)]
		return ordered[f] + (ordered[c] - ordered[f]) * (k - f)
