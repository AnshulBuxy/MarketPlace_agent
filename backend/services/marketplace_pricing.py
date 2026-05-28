from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path
from typing import Any


_PRICE_DATA_PATH = Path(__file__).resolve().parents[1] / "agents" / "PriceData.json"


def _normalize_text(text: str) -> str:
	return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", text.lower())).strip()


def _tokenize(text: str) -> set[str]:
	stopwords = {
		"the",
		"and",
		"with",
		"for",
		"from",
		"that",
		"this",
		"made",
		"of",
		"a",
		"an",
		"in",
		"to",
		"is",
		"are",
		"product",
		"handmade",
		"handcrafted",
		"craft",
	}
	return {token for token in _normalize_text(text).split() if token and token not in stopwords}


def _similarity(query: str, candidate: str) -> float:
	query_norm = _normalize_text(query)
	candidate_norm = _normalize_text(candidate)
	if not query_norm or not candidate_norm:
		return 0.0
	sequence_score = SequenceMatcher(None, query_norm, candidate_norm).ratio()
	query_tokens = _tokenize(query)
	candidate_tokens = _tokenize(candidate)
	if not query_tokens or not candidate_tokens:
		return sequence_score
	overlap = len(query_tokens & candidate_tokens) / max(len(query_tokens | candidate_tokens), 1)
	return round((sequence_score * 0.7) + (overlap * 0.3), 4)


@lru_cache(maxsize=1)
def _load_price_data() -> list[dict[str, Any]]:
	with _PRICE_DATA_PATH.open("r", encoding="utf-8") as handle:
		return json.load(handle)


def _parse_price(value: Any) -> int | None:
	if value is None:
		return None
	if isinstance(value, (int, float)):
		return int(value)
	clean = re.sub(r"[^0-9]", "", str(value))
	return int(clean) if clean else None


def _domain_bias(query: str, candidate: str) -> float:
	query_norm = _normalize_text(query)
	candidate_norm = _normalize_text(candidate)
	art_keywords = {"painting", "paint", "art", "wall", "canvas", "decor", "décor", "frame", "framed", "mural", "illustration"}
	fashion_keywords = {"saree", "sari", "silk", "blouse", "pallu", "lehenga", "kurta", "dupatta"}
	query_tokens = set(query_norm.split())
	candidate_tokens = set(candidate_norm.split())

	query_is_art = bool(query_tokens & art_keywords)
	query_is_fashion = bool(query_tokens & fashion_keywords)
	candidate_is_art = bool(candidate_tokens & art_keywords)
	candidate_is_fashion = bool(candidate_tokens & fashion_keywords)

	bias = 0.0
	if query_is_art:
		if candidate_is_art:
			bias += 0.28
		if candidate_is_fashion:
			bias -= 0.45
	if query_is_fashion:
		if candidate_is_fashion:
			bias += 0.28
		if candidate_is_art:
			bias -= 0.45

	# Extra nudge when the candidate clearly matches the same visual category.
	if query_is_art and {"painting", "wall", "canvas", "art"} & candidate_tokens:
		bias += 0.12
	if query_is_fashion and {"saree", "silk", "pallu", "blouse"} & candidate_tokens:
		bias += 0.12

	return bias


def find_marketplace_matches(product_name: str, description: str, limit: int = 4) -> list[dict[str, Any]]:
	query = f"{product_name} {description}".strip()
	items = _load_price_data()
	matched_items: list[dict[str, Any]] = []
	for item in items:
		candidate = f"{item.get('product_name', '')} {item.get('description', '')}"
		score = min(max(_similarity(query, candidate) + _domain_bias(query, candidate), 0.0), 1.0)
		matched_items.append(
			{
				"productName": item.get("product_name", ""),
				"description": item.get("description", ""),
				"marketplaceName": item.get("marketplace_name", ""),
				"price": _parse_price(item.get("price")),
				"link": item.get("link", ""),
				"score": score,
			}
		)
	matched_items.sort(key=lambda entry: entry["score"], reverse=True)
	return matched_items[:limit]