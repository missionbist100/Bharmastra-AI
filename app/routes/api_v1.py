"""Versioned API router for Bharmastra-AI.

This module registers sub-routers for:
 - research
 - compare/analyze
 - project planning
 - backend generation
 - code review
 - conversation/chat
 - auth (JWT)

Each module lives in app.routes.<module> and exposes an APIRouter named `router`.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

# Sub-routers (implemented in subsequent files)
# These imports are intentionally explicit so file creation order is clear.
# Each submodule will provide an `router: APIRouter` object.
from app.routes import (
    auth,
    research,
    planning,
    backend_generation,
    code_review,
    conversation,
)

router = APIRouter(tags=["API", "v1"])


@router.get("/", summary="API root")
async def api_root():
    """
    Root for API version v1. Returns a small summary and link to docs.
    """
    return {"service": "Bharmastra-AI", "version": "v1", "docs": "/docs"}


@router.get("/health", summary="Service health check")
async def health():
    return {"status": "ok"}


# Include subrouters with clear prefixes and tags.
# Each router file will declare its own tags and path operation details.
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(research.router, prefix="/research", tags=["research"])
router.include_router(planning.router, prefix="/planning", tags=["planning"])
router.include_router(backend_generation.router, prefix="/generate", tags=["backend-generation"])
router.include_router(code_review.router, prefix="/review", tags=["code-review"])
router.include_router(conversation.router, prefix="/chat", tags=["conversation"])

# Example global exception handler for API v1 (can be overridden later)
@router.exception_handler(Exception)
async def api_v1_exception_handler(request: Request, exc: Exception):
    # Keep responses uniform in the API surface
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred."},
    )
