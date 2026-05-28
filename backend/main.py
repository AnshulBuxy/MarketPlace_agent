"""FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import admin, health, webhook, orchestrator

def create_app() -> FastAPI:
	"""Build the FastAPI application."""
	app = FastAPI(title="Riyaaz API")
	
	# Allow frontend to access API
	app.add_middleware(
		CORSMiddleware,
		allow_origins=["*"],
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)

	app.include_router(health.router)
	app.include_router(webhook.router)
	app.include_router(admin.router)
	app.include_router(orchestrator.router)
	return app


app = create_app()
