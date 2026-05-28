from __future__ import annotations

import ssl
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings


def build_connect_args(database_url: str) -> dict[str, object]:
    """Return asyncpg connect args for the configured database URL."""
    if "sslmode=disable" in database_url:
        return {"ssl": False}

    if "sslmode=require" in database_url or "supabase.co" in database_url:
        context = ssl._create_unverified_context()
        context.check_hostname = False
        return {"ssl": context}

    return {}


_settings = get_settings()
_engine: AsyncEngine = create_async_engine(
    _settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args=build_connect_args(_settings.database_url),
)
AsyncSessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
