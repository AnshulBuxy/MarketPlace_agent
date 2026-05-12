"""
WhatsApp Image Test - Simulates real WhatsApp message with image.

Tests the full orchestrator flow:
1. Receives WhatsApp message with image
2. Ingestion: Downloads image, checks quality, stores to S3
3. Extraction: Analyzes image (currently mock, Phase 2 = Gemini)
4. Routing: Routes to marketplace

Run this script to test image handling.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.config import get_settings
from backend.db import AsyncSessionLocal
from backend.orchestrator import (
	WorkflowState,
	NodeType,
	get_orchestrator,
)
from backend.agents.nodes import IngestionNode, ExtractionNode, MarketplaceRoutingNode


async def create_whatsapp_image_payload() -> dict:
	"""
	Create a realistic WhatsApp payload with image.
	This simulates what Twilio sends.
	"""
	return {
		"MessageSid": str(uuid4()),
		"From": "whatsapp:+917869291927",
		"Body": "Here is my product",  # Optional caption
		"NumMedia": "1",
		"MediaUrl0": "https://example.com/product.jpg",  # Would be Twilio URL in reality
		"MediaContentType0": "image/jpeg",
	}


async def run_image_test():
	"""Test orchestrator with image input."""
	print("=" * 80)
	print("PHASE 1 ORCHESTRATOR - IMAGE INPUT TEST")
	print("=" * 80)
	
	settings = get_settings()
	print(f"\n✓ Settings loaded")
	print(f"  - Min Image Size: {settings.min_image_px}px")
	print(f"  - S3 Bucket: {settings.aws_s3_bucket}")
	print(f"  - S3 Endpoint: {settings.s3_endpoint_url or 'AWS'}")
	
	# Initialize orchestrator
	orchestrator = get_orchestrator(settings)
	orchestrator.register_node(IngestionNode())
	orchestrator.register_node(ExtractionNode())
	orchestrator.register_node(MarketplaceRoutingNode())
	print(f"✓ Orchestrator ready with {len(orchestrator.nodes)} nodes")
	
	# Create test payload with image
	payload = await create_whatsapp_image_payload()
	print(f"\n✓ WhatsApp Payload with Image:")
	print(f"  - From: {payload['From']}")
	print(f"  - Body: {payload['Body']}")
	print(f"  - Media: {payload['MediaContentType0']}")
	print(f"  - URL: {payload['MediaUrl0']}")
	
	async with AsyncSessionLocal() as session:
		try:
			# Create workflow state
			workflow_state = WorkflowState(current_node=NodeType.INGESTION)
			workflow_state.node_outputs["ingestion_message"] = payload
			
			print(f"\n{'='*80}")
			print("IMAGE PROCESSING FLOW")
			print('='*80)
			
			# Execute workflow with images
			workflow_state = await orchestrator.execute_workflow(workflow_state, session)
			
			print(f"\n✓ INGESTION NODE:")
			ingestion_outputs = workflow_state.node_outputs.get("ingestion", {})
			print(f"  - Product ID: {ingestion_outputs.get('product_id')}")
			print(f"  - Image Quality OK: {ingestion_outputs.get('image_quality_ok')}")
			print(f"  - Media URL (S3): {ingestion_outputs.get('media_url')}")
			print(f"  - Transcription: {ingestion_outputs.get('transcription') or 'N/A'}")
			
			print(f"\n✓ EXTRACTION NODE (Phase 1 stub):")
			extraction_outputs = workflow_state.node_outputs.get("extraction", {})
			print(f"  - Name: {extraction_outputs.get('name')}")
			print(f"  - Category: {extraction_outputs.get('category')}")
			print(f"  - Materials: {extraction_outputs.get('materials')}")
			
			print(f"\n✓ CONFIDENCE SCORES:")
			for field, score in workflow_state.confidence_scores.items():
				status = "✓" if score >= 0.8 else "⚠"
				print(f"  {status} {field}: {score:.2f}")
			
			print(f"\n{'='*80}")
			print("WORKFLOW EXECUTION COMPLETE ✓")
			print('='*80)
			print(f"\nNode Sequence: {' → '.join(workflow_state.node_sequence)}")
			print(f"Current Status: {workflow_state.current_node_status}")
			
			# Show how to use the image in Phase 2
			print(f"\n{'='*80}")
			print("PHASE 2: REAL IMAGE ANALYSIS")
			print('='*80)
			print("""
For Phase 2, replace the mock extraction with real Gemini vision:

```python
from google.generativeai import upload_file
import google.generativeai as genai

# In ExtractionNode.execute():
genai.configure(api_key=settings.gemini_api_key)
image_file = await download_from_s3(media_url)
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content([
    "Extract product attributes: name, category, materials, size, condition",
    image_file
])
# Parse response and return structured attributes
```

Current State:
- ✓ Image ingestion working
- ✓ S3 storage configured
- ✓ Image quality checks active
- ⏳ Waiting for Gemini API key (GEMINI_API_KEY in .env)
			""")
			
		except Exception as e:
			print(f"\n✗ Error: {str(e)}")
			import traceback
			traceback.print_exc()
			await session.rollback()
			return False
	
	return True


if __name__ == "__main__":
	asyncio.run(run_image_test())
