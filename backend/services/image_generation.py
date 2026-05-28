import logging
import io
from fastapi import HTTPException
from huggingface_hub import AsyncInferenceClient
from ..config import Settings

logger = logging.getLogger(__name__)

class ImageGenerationService:
    def __init__(self, settings: Settings):
        self._settings = settings
        self.token = settings.huggingface_api_token
        self.model = settings.hf_vision_model
        
        self.client = None
        if self.token:
            self.client = AsyncInferenceClient(
                provider="fal-ai",
                api_key=self.token
            )

    async def generate_image_to_image(self, prompt: str, base_image_bytes: bytes) -> bytes:
        """
        Uses HuggingFace InferenceClient with fal-ai provider for FLUX.2-dev
        """
        if not self.client or not self.model:
            raise ValueError("HuggingFace API token or Vision Model is not configured.")

        try:
            # We call image_to_image which internally hits the external provider
            img = await self.client.image_to_image(
                base_image_bytes,
                prompt=prompt,
                model=self.model,
            )
            
            # The client returns a PIL image if Pillow is installed
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
            
        except Exception as e:
            logger.error(f"ImageGenerationService error: {e}")
            raise HTTPException(status_code=502, detail=f"Image generation failed: {e}")
