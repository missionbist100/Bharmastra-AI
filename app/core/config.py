"""app/core/config.py

Configuration for Bharmastra-AI.

- Uses Pydantic BaseSettings to load values from environment variables.
- Central place for settings used across app.main, auth, DB, and AI providers.
- Keep secrets out of source control; use a .env in development and a secure secrets manager in production.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings, EmailStr, Field, PostgresDsn, validator


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "Bharmastra-AI"
    ENV: str = "development"
    DEBUG: bool = False

    # Security / Auth
    SECRET_KEY: str = Field(..., description="JWT secret key. Must be set in production.")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour

    # Database (asyncpg-compatible SQLAlchemy URL)
    DATABASE_URL: PostgresDsn = Field(
        "postgresql+asyncpg://bharmastra:bharmastra@db:5432/bharmastra",
        description="Async SQLAlchemy database URL (postgresql+asyncpg://...)",
    )
    SQLALCHEMY_ECHO: bool = False

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default_factory=lambda: ["http://localhost", "http://localhost:3000"]
    )

    # Rate limiting (MVP; replace with redis-backed limiter in prod)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # AI provider selection and keys (provider-agnostic)
    AI_PROVIDER: str = "openai"  # openai | anthropic | gemini | ollama
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OLLAMA_URL: Optional[str] = None  # e.g., http://localhost:11434

    # Optional observability
    SENTRY_DSN: Optional[AnyHttpUrl] = None
    DEFAULT_FROM_EMAIL: Optional[EmailStr] = None

    # Other
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def _assemble_cors_origins(cls, v):
        """
        Accepts a JSON/CSV string or list. Examples:
        - 'http://localhost,https://example.com'
        - '["http://localhost","https://example.com"]'
        """
        if isinstance(v, str):
            # comma-separated
            origins = [o.strip() for o in v.split(",") if o.strip()]
            return origins
        return v

    @validator("DATABASE_URL", pre=True)
    def _ensure_async_dsn(cls, v):
        """
        Ensure the DATABASE_URL uses asyncpg driver. If a normal postgres URL is provided,
        attempt to convert it to asyncpg scheme.
        """
        if isinstance(v, str) and v.startswith("postgres://"):
            # Convert to postgresql+asyncpg://
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        return v


# singleton settings instance imported across the app
settings = Settings()
