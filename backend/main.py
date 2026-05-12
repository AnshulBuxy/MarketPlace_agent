"""FastAPI application entrypoint."""

from fastapi import FastAPI

from .api import admin, health, webhook, orchestrator


def create_app() -> FastAPI:
	"""Build the FastAPI application."""
	app = FastAPI(title="Riyaaz API")
	app.include_router(health.router)
	app.include_router(webhook.router)
	app.include_router(admin.router)
	app.include_router(orchestrator.router)
	return app


app = create_app()
