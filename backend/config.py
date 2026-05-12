from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
	"""Application settings loaded from environment."""

	model_config = SettingsConfigDict(
		env_file=str(_REPO_ROOT / ".env"),
		env_file_encoding="utf-8",
	)

	env: str = "local"
	app_name: str = "riyaaz"
	database_url: str
	redis_url: str
	celery_broker_url: str
	celery_result_backend: str
	use_celery_for_ingestion: bool = False
	http_timeout_seconds: int = 30
	http_max_retries: int = 3
	min_image_px: int = 500
	min_blur_variance: float = 50.0

	aws_access_key_id: str | None = None
	aws_secret_access_key: str | None = None
	aws_s3_bucket: str
	aws_region: str = "ap-south-1"
	s3_endpoint_url: str | None = None
	aws_role_arn: str | None = None
	aws_role_session_name: str = "riyaaz-session"
	s3_public_base_url: str | None = None

	gupshup_api_key: str | None = None
	gupshup_app_name: str | None = None
	whatsapp_webhook_verify_token: str | None = None
	twilio_account_sid: str | None = None
	twilio_auth_token: str | None = None
	twilio_whatsapp_number: str | None = None

	google_api_key: str | None = None
	google_gemini_flash_model: str = "gemini-1.5-flash"
	groq_api_key: str | None = None
	groq_fast_routing_model: str = "llama3-70b-8192"
	huggingface_api_token: str | None = None
	hf_inference_base_url: str = "https://api-inference.huggingface.co/models"
	hf_text_model: str | None = None
	hf_vision_model: str | None = None
	hf_image_model: str = "black-forest-labs/FLUX.1-schnell"

	openai_api_key: str | None = None
	whisper_model: str = "whisper-1"
	google_tts_api_key: str | None = None
	elevenlabs_api_key: str | None = None

	ebay_client_id: str | None = None
	ebay_client_secret: str | None = None
	ebay_marketplace_id: str = "EBAY_US"
	ebay_oauth_scope: str = "https://api.ebay.com/oauth/api_scope"
	fx_rate_base_url: str = "https://api.exchangerate.host/latest"
	fx_rate_inr_per_usd: float | None = None

	message_templates_path: str = "backend/prompts/messages.json"


@lru_cache
def get_settings() -> Settings:
	"""Return cached settings."""
	return Settings()


def load_message_templates() -> dict:
	"""Load message templates from JSON file."""
	settings = get_settings()
	path = Path(settings.message_templates_path)
	if not path.is_absolute():
		path = _REPO_ROOT / path
	if not path.exists():
		return {}
	return json.loads(path.read_text(encoding="utf-8"))
