import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.config import get_settings
from backend.services.marketplace_connectors.google_lens import GoogleLensConnector
from backend.services.marketplace_connectors.base import SearchQuery

async def test_google_lens():
    settings = get_settings()
    connector = GoogleLensConnector(settings)
    
    if not settings.serpapi_api_key:
        print("❌ Error: SERPAPI_API_KEY not found in .env")
        return

    print("--- Google Lens Search Agent Test ---")
    
    # 1. Image Search (provide a public URL or local path)
    image_arg = sys.argv[1] if len(sys.argv) > 1 else "https://i.ebayimg.com/images/g/H~AAAOSw-~Rk~o~m/s-l1600.jpg"
    
    print(f"\nTesting Google Lens Visual Search for: \n{image_arg}")
    try:
        image_url = None
        image_bytes = None
        mime_type = None
        
        image_path = Path(image_arg)
        if image_path.exists() and image_path.is_file():
            import mimetypes
            print(f"Reading local image file: {image_arg}...")
            image_bytes = image_path.read_bytes()
            mime_type = mimetypes.guess_type(image_arg)[0]
        else:
            print(f"Using provided URL: {image_arg}...")
            image_url = image_arg

        query = SearchQuery(keywords="", image_url=image_url, image_bytes=image_bytes, mime_type=mime_type, limit=10)
        results = await connector.search_listings(query)
        
        print(f"\n✅ Found {len(results)} visual matches across marketplaces:")
        for i, r in enumerate(results):
            print(f"{i+1}. {r.title}")
            print(f"   Price: {r.currency} {r.price}")
            print(f"   Source: {r.source}")
            print(f"   URL: {r.url}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ Google Lens search failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_google_lens())
