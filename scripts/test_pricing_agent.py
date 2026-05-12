r"""Standalone test for the eBay pricing agent.

Usage:
    .\.venv\Scripts\python.exe scripts\test_pricing_agent.py \
        --description "handmade jute bag" \
        --attributes-json "{\"category\":\"handmade bag\",\"materials\":[\"jute\"],\"tags\":[\"woven\"]}"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path for backend imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.config import get_settings
from backend.services.pricing_agent import PriceRequest, PricingAgent


def _load_attributes(payload: str | None) -> dict:
    if not payload:
        return {}
    return json.loads(payload)


def main() -> int:
    parser = argparse.ArgumentParser(description="Test eBay pricing agent.")
    parser.add_argument("--description", default="", help="Product description")
    parser.add_argument("--attributes-json", default="{}", help="Attributes JSON string")
    parser.add_argument("--image-url", default=None, help="Optional image URL")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()

    settings = get_settings()
    attributes = _load_attributes(args.attributes_json)

    request = PriceRequest(
        image_url=args.image_url,
        description=args.description,
        attributes=attributes,
    )

    async def _run() -> int:
        agent = PricingAgent(settings)
        response = await agent.run(request, limit=args.limit, top_n=args.top_n)
        print("Suggested price (INR):", response.suggested_price_inr)
        print("Range (INR):", response.min_price_inr, "-", response.max_price_inr)
        print("Confidence:", response.confidence)
        print("Matches:")
        for match in response.matches:
            print("-", match.title)
            print("  Price INR:", match.price_inr)
            print("  URL:", match.url)
        return 0

    return asyncio.run(_run())


if __name__ == "__main__":
    sys.exit(main())
