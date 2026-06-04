"""Test Groq vision extraction with a local image file."""
import asyncio
import base64
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from groq import Groq
from backend.config import get_settings

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

def test_with_url():
    """Test using a public image URL (simpler, no base64 needed)."""
    print(f"\n=== Testing Groq Vision ({MODEL}) with URL ===")
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/280px-PNG_transparency_demonstration_1.png"
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": url}},
            ],
        }],
    )
    text = response.choices[0].message.content or ""
    print("Raw response:")
    print(text[:500])
    return text

def test_with_local_file(image_path: str):
    """Test using a local image file encoded as base64."""
    print(f"\n=== Testing Groq Vision ({MODEL}) with local file: {image_path} ===")
    img_bytes = Path(image_path).read_bytes()
    mime = "image/jpeg" if image_path.endswith((".jpg", ".jpeg")) else "image/png"
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    data_url = f"data:{mime};base64,{b64}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": PROMPT},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
    )
    text = response.choices[0].message.content or ""
    print("Raw response:")
    print(text[:1000])
    return text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # python scripts/test_groq_vision.py path/to/image.jpg
        test_with_local_file(sys.argv[1])
    else:
        test_with_url()
