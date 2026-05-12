r"""Test Gemini text and multimodal capability using an image from S3.

Usage:
    .\.venv\Scripts\python.exe scripts\test_gemini_multimodal.py --s3-key products/<id>/image.jpg

Options:
    --s3-key       S3 object key inside the bucket (recommended).
    --s3-url       S3 URL like s3://bucket/key (optional).
    --bucket       Override bucket name (defaults to AWS_S3_BUCKET in .env).
    --model        Override Gemini model name (defaults to GOOGLE_GEMINI_FLASH_MODEL).
    --prompt       Custom prompt for multimodal test.
"""

from __future__ import annotations

import argparse
import asyncio
import mimetypes
import sys
from pathlib import Path
from typing import Optional, Tuple

import boto3
import google.generativeai as genai

# Ensure repo root is on sys.path for backend imports
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select

from backend.config import get_settings
from backend.db import AsyncSessionLocal
from backend.models.product import Product


def _parse_s3_url(s3_url: str) -> Tuple[str, str]:
    if not s3_url.startswith("s3://"):
        raise ValueError("--s3-url must start with s3://")
    path = s3_url.replace("s3://", "", 1)
    if "/" not in path:
        raise ValueError("--s3-url must be in the form s3://bucket/key")
    bucket, key = path.split("/", 1)
    return bucket, key


def _download_from_s3(
    bucket: str,
    key: str,
    region: str,
    endpoint_url: Optional[str],
    access_key: Optional[str],
    secret_key: Optional[str],
    session_token: Optional[str],
) -> bytes:
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region,
    )
    client = session.client("s3", endpoint_url=endpoint_url or None)
    response = client.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def _extract_bucket_key_from_url(image_url: str) -> Tuple[str, str]:
    if image_url.startswith("s3://"):
        return _parse_s3_url(image_url)
    raise ValueError("Image URL is not an s3:// URL. Provide --s3-key or --s3-url.")


async def _get_latest_image_url() -> Optional[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Product)
            .where(Product.image_url.is_not(None))
            .order_by(Product.created_at.desc())
            .limit(1)
        )
        product = result.scalar_one_or_none()
        return product.image_url if product else None


def _guess_mime_type(key: str) -> str:
    mime, _ = mimetypes.guess_type(key)
    return mime or "image/jpeg"


def main() -> int:
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Test Gemini text and multimodal capability.")
    parser.add_argument("--s3-key", help="S3 object key inside the bucket.")
    parser.add_argument("--s3-url", help="S3 URL like s3://bucket/key")
    parser.add_argument("--bucket", help="Override bucket name")
    parser.add_argument("--model", help="Override Gemini model name")
    parser.add_argument("--prompt", default="Describe the image in one sentence.")
    args = parser.parse_args()

    if not settings.google_api_key:
        print("Missing GOOGLE_API_KEY in .env")
        return 1

    bucket = args.bucket or settings.aws_s3_bucket
    key = None

    if args.s3_url:
        bucket, key = _parse_s3_url(args.s3_url)
    elif args.s3_key:
        key = args.s3_key
    else:
        image_url = asyncio.run(_get_latest_image_url())
        if not image_url:
            print("No product image found in DB. Provide --s3-key or --s3-url.")
            return 1
        try:
            bucket, key = _extract_bucket_key_from_url(image_url)
        except ValueError as exc:
            print(str(exc))
            return 1

    if not bucket or not key:
        print("Bucket or key is empty")
        return 1

    print(f"Using bucket: {bucket}")
    print(f"Using key: {key}")

    try:
        image_bytes = _download_from_s3(
            bucket=bucket,
            key=key,
            region=settings.aws_region,
            endpoint_url=settings.s3_endpoint_url or None,
            access_key=settings.aws_access_key_id,
            secret_key=settings.aws_secret_access_key,
            session_token=None,
        )
        print(f"Downloaded image bytes: {len(image_bytes)}")
    except Exception as exc:
        print(f"Failed to download from S3: {exc}")
        return 1

    genai.configure(api_key=settings.google_api_key)
    model_name = args.model or settings.google_gemini_flash_model or "gemini-1.5-flash"
    model = genai.GenerativeModel(model_name)

    # Text-only test
    try:
        text_response = model.generate_content("Reply with the word OK only.")
        print("Text-only response:")
        print(text_response.text)
    except Exception as exc:
        print(f"Text-only call failed: {exc}")
        return 1

    # Multimodal test
    mime_type = _guess_mime_type(key)
    try:
        response = model.generate_content([
            args.prompt,
            {"mime_type": mime_type, "data": image_bytes},
        ])
        print("Multimodal response:")
        print(response.text)
        print("Multimodal test succeeded.")
        return 0
    except Exception as exc:
        print(f"Multimodal call failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
