"""SQLAlchemy async models and DB utilities for Bharmastra-AI.

This module provides a small wrapper around SQLAlchemy async engine and a `get_db`
dependency used across route handlers.

Database models are defined under app.models.* (e.g., user.py). Importing them here
helps avoid circular imports in route modules.
"""
from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings

_engine: AsyncEngine | None = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


def init_engine() -> None:
    """Initialize the global engine and session maker.

    This function should be invoked during application startup.
    """
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQLALCHEMY_ECHO, future=True)
        _SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async DB session for request handlers.

    If the engine/session maker has not been initialized, this function will initialize it on demand.
    """
    global _SessionLocal
    if _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None
    async with _SessionLocal() as session:
        yield session
