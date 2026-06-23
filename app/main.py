"""app/main.py

FastAPI application factory and entrypoint for Bharmastra-AI.

Responsibilities:
- Create FastAPI app instance
- Configure logging, CORS, middleware, exception handlers
- Initialize async SQLAlchemy engine/session
- Register API routers under /api/v1
- Provide simple in-memory rate limiter (MVP)

This file follows dependency inversion: auth, DB, and routers are provided by modules in app.core, app.db, and app.routes respectively.
"""

from __future__ import annotations

import logging
import os
import time
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings

# Routers are kept in app.routes - each router will be registered under /api/v1
# Import lazily inside create_app() to avoid import-time side effects when testing.

logger = logging.getLogger("bharmastra")


class SimpleRateLimiter:
    """A simple in-memory rate limiter for demonstration purposes.

    This is NOT suitable for multi-process or production use. Replace with
    Redis or a distributed rate limiter for production workloads.
    """

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        # store: key -> list[timestamp]
        self._store: dict[str, list[float]] = {}

    async def is_allowed(self, key: str) -> bool:
        """Return True if request from `key` is allowed, otherwise False."""
        now = time.time()
        window_start = now - self.window
        arr = self._store.get(key, [])
        # drop old timestamps
        arr = [t for t in arr if t >= window_start]
        if len(arr) >= self.max_requests:
            self._store[key] = arr
            return False
        arr.append(now)
        self._store[key] = arr
        return True


rate_limiter = SimpleRateLimiter(max_requests=settings.RATE_LIMIT_REQUESTS, window_seconds=settings.RATE_LIMIT_WINDOW)


# Database engine/session will be created during startup
_engine = None
_SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session for request handlers.

    Uses the async sessionmaker created during startup.
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized - did you call create_app()?")
    async with _SessionLocal() as session:
        yield session


async def rate_limit_dependency(request: Request):
    """Dependency that enforces rate limiting per client. Uses Authorization header
    if provided, otherwise falls back to client IP.
    """
    # Prefer Authorization identity if present
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        key = auth[7:]
    else:
        # fallback to client host
        client = request.client.host if request.client else "anonymous"
        key = f"ip:{client}"

    allowed = await rate_limiter.is_allowed(key)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


def create_app() -> FastAPI:
    """Application factory for testing and production.

    Returns:
        FastAPI instance with configured routers and middleware.
    """
    app = FastAPI(
        title="Bharmastra-AI",
        description="AI-powered coding and research assistant",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger.info("Starting Bharmastra-AI application")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handlers
    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception for request: %s", request.url)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    # Health check
    @app.get("/healthz", tags=["Health"])
    async def healthz():
        return {"status": "ok"}

    # Versioned API router registration (lazy import)
    from app.routes import api_v1

    app.include_router(api_v1.router, prefix="/api/v1", dependencies=[Depends(rate_limit_dependency)])

    # Startup/shutdown events to initialize DB connection
    @app.on_event("startup")
    async def on_startup():
        nonlocal _engine, _SessionLocal
        # Create async engine
        database_url = settings.DATABASE_URL
        logger.info("Connecting to database: %s", database_url)
        _engine = create_async_engine(database_url, echo=settings.SQLALCHEMY_ECHO, future=True)
        _SessionLocal = async_sessionmaker(_engine, expire_on_commit=False)
        # Optionally run migrations here or perform checks

    @app.on_event("shutdown")
    async def on_shutdown():
        nonlocal _engine
        if _engine is not None:
            await _engine.dispose()
            logger.info("Database connection pool disposed")

    return app


app = create_app()


if __name__ == "__main__":
    # Simple entrypoint for local runs. Use uvicorn in production.
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), log_level="info")
