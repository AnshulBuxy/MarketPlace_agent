# Riyaaz MVP (Scaffold)

This repo contains the Phase 1 scaffolding for the Riyaaz backend and the existing
Admin_Dashboard frontend.

## Structure
- Admin_Dashboard/ (existing frontend)
- backend/ (FastAPI backend scaffold)
- scripts/ (seeders and simulation placeholders)

## Environment
Copy .env.example to .env and fill in required keys.

## Phase 1 Setup (Local)
1. Start infrastructure: `docker-compose up -d`
2. Install backend deps: `pip install -r backend/requirements.txt`
3. Run migrations: `cd backend` then `alembic upgrade head`
4. Start API: `uvicorn backend.main:app --reload --port 8000`
5. Optional: start Celery worker: `celery -A backend.tasks.orchestrator worker --loglevel=info`

## WhatsApp (Twilio)
- Use a Twilio WhatsApp sandbox and point the webhook to `/webhook/whatsapp`.
- For local testing, expose the API with ngrok and add the public URL in Twilio.
- Set `USE_CELERY_FOR_INGESTION=true` if you want webhook to enqueue ingestion.

## Notes
- LLMs: Gemini Flash for main/vision, Hugging Face for open models, Groq for fast routing.
- This scaffold only sets up structure; implementation starts in Phase 1.
