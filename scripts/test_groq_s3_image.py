"""
Test Groq vision directly with the enhanced image from S3.
Usage: python scripts/test_groq_s3_image.py <s3_url_or_product_id>
"""
import asyncio
import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groq import Groq
from backend.config import get_settings
from backend.services.storage import StorageService

settings = get_settings()
client = Groq(api_key=settings.groq_api_key)
MODEL = settings.groq_vision_model

PROMPT = (
    "You are a product attribute extractor. Return ONLY valid JSON with the following fields: "
    "name (string), category (string), materials (array of strings), "
    "dimensions (object with length,width,height,unit or note), "
    "description (string), tags (array of strings), "
    "confidence (object with name,category,materials,dimensions,description values between 0 and 1). "
    "Do not include any extra text outside JSON."
)


async def main():
    storage = StorageService(settings)

    if len(sys.argv) < 2:
        print("Usage: python scripts/test_groq_s3_image.py <s3://bucket/key>")
        print("       python scripts/test_groq_s3_image.py <product_uuid>")
        sys.exit(1)

    arg = sys.argv[1]

    # If it's a product UUID, look up its image from DB
    if not arg.startswith("s3://") and not arg.startswith("http"):
        from backend.db import AsyncSessionLocal
        from backend.models.product import Product
        from uuid import UUID
        async with AsyncSessionLocal() as session:
            product = await session.get(Product, UUID(arg))
            if not product:
                print(f"Product {arg} not found")
                sys.exit(1)
            url = product.image_url_enhanced or product.image_url
            print(f"Product image_url_enhanced: {product.image_url_enhanced}")
            print(f"Product image_url:          {product.image_url}")
            print(f"Using: {url}")
    else:
        url = arg

    print(f"\nDownloading image from: {url}")
    image_bytes = await storage.download_bytes_from_url(url)
    print(f"Downloaded: {len(image_bytes)} bytes")

    # Check the first few bytes to detect actual format
    header = image_bytes[:16]
    print(f"First 16 bytes (hex): {header.hex()}")
    if image_bytes[:2] == b'\xff\xd8':
        print("Format detected: JPEG ✓")
        mime = "image/jpeg"
    elif image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        print("Format detected: PNG")
        mime = "image/png"
    elif image_bytes[:4] == b'RIFF':
        print("Format detected: WEBP")
        mime = "image/webp"
    else:
        print("Format detected: UNKNOWN — this is likely the problem!")
        mime = "image/jpeg"  # try anyway

    # Save locally to inspect
    out_path = Path("scripts/debug_s3_image.jpg")
    out_path.write_bytes(image_bytes)
    print(f"Saved to {out_path} — open it to verify it looks correct")

    # Send to Groq
    print(f"\nSending to Groq ({MODEL})...")
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ],
        }],
    )
    text = response.choices[0].message.content or ""
    print(f"\nGroq raw response:\n{text}")


if __name__ == "__main__":
    asyncio.run(main())
