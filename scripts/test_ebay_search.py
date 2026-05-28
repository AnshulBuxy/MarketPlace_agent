import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from backend.config import get_settings
from backend.services.marketplace_connectors.ebay import EbayConnector
from backend.services.marketplace_connectors.base import SearchQuery
from backend.services.storage import StorageService

async def test_ebay_search():
    settings = get_settings()
    connector = EbayConnector(settings)
    storage = StorageService(settings)
    
    print("--- eBay Search Agent Test ---")
    
    # 1. Test Keyword Search
    keyword = "Handcrafted Brass Pen Holder"
    print(f"\n1. Testing Keyword Search: '{keyword}'")
    try:
        query = SearchQuery(keywords=keyword, limit=5)
        results = await connector.search_listings(query)
        print(f"Found {len(results)} results:")
        for r in results:
            print(f"- {r.title} ({r.currency} {r.price})")
    except Exception as e:
        print(f"❌ Keyword search failed: {e}")
        print("Check your eBay credentials in .env")

    # 2. Test Image Search (if image provided via command line)
    image_url = sys.argv[1] if len(sys.argv) > 1 else None
    if image_url:
        print(f"\n2. Testing Image Search: '{image_url}'")
        try:
            image_path = Path(image_url)
            if image_path.exists() and image_path.is_file():
                print("Reading local image file...")
                image_bytes = image_path.read_bytes()
            else:
                print("Downloading image bytes via StorageService...")
                image_bytes = await storage.download_bytes_from_url(image_url)
            
            query = SearchQuery(keywords=keyword, image_bytes=image_bytes, limit=5)
            results = await connector.search_listings(query)
            
            print(f"Found {len(results)} results via visual search:")
            for r in results:
                print(f"- {r.title} ({r.currency} {r.price})")
                print(f"  URL: {r.url}")
        except Exception as e:
            print(f"❌ Image search failed: {e}")
            print("Note: eBay search_by_image requires valid Production credentials for the Buy API.")
    else:
        print("\n2. Skipping Image Search (no image URL provided)")
        print("Usage: python scripts/test_ebay_search.py <image_url>")

if __name__ == "__main__":
    asyncio.run(test_ebay_search())
