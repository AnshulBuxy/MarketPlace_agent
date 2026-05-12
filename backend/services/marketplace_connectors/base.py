from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class Listing:
	"""Normalized listing from a marketplace."""

	title: str
	price: float
	currency: str
	url: str
	image_url: str | None
	condition: str | None
	shipping_price: float | None
	shipping_currency: str | None
	source: str
	raw: dict[str, Any]


@dataclass
class SearchQuery:
	"""Basic search query for marketplace listing search."""

	keywords: str
	limit: int = 20


class MarketplaceConnector(Protocol):
	"""Connector interface for marketplaces."""

	async def search_listings(self, query: SearchQuery) -> list[Listing]:
		...
