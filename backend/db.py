from __future__ import annotations

import ssl
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from .config import get_settings


def build_connect_args(database_url: str | None) -> dict[str, object]:
    """Return asyncpg connect args for the configured database URL."""
    if not database_url:
        return {}

    if "sslmode=disable" in database_url:
        return {"ssl": False}

    if "sslmode=require" in database_url or "supabase.co" in database_url:
        context = ssl._create_unverified_context()
        context.check_hostname = False
        return {"ssl": context}

    return {}


_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = settings.database_url
        if not db_url:
            raise ValueError(
                "DATABASE_URL is not configured! Please configure it in your environment."
            )
        # Strip potential surrounding quotes from Vercel env var pasting
        db_url = db_url.strip("'\"")
        _engine = create_async_engine(
            db_url,
            pool_pre_ping=True,
            future=True,
            connect_args=build_connect_args(db_url),
        )
    return _engine


class LazyAsyncSessionMaker:
    def __init__(self):
        self._maker = None

    def _get_maker(self):
        if self._maker is None:
            self._maker = async_sessionmaker(get_engine(), expire_on_commit=False)
        return self._maker

    def __call__(self, *args, **kwargs):
        return self._get_maker()(*args, **kwargs)


AsyncSessionLocal = LazyAsyncSessionMaker()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
