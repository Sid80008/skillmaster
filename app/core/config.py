"""
Application configuration.

All settings are read from environment variables (or a .env file).
No hardcoded secrets, no mutable global state.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object.  Loaded once and cached."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://skillquest:password@localhost/skillquest",
        description="PostgreSQL DSN used by the application.",
    )
    test_database_url: str = Field(
        default="postgresql://skillquest:password@localhost/skillquest_test",
        description="Separate PostgreSQL DSN used during pytest runs.",
    )

    # ── Auth / JWT ────────────────────────────────────────────────────────
    secret_key: str = Field(
        min_length=32,
        description="JWT signing secret.  Must be at least 32 characters.",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # ── Application ───────────────────────────────────────────────────────
    environment: Literal["development", "testing", "production"] = "development"
    log_level: Literal["debug", "info", "warning", "error"] = "info"
    frontend_url: str = Field(default="http://localhost:5173")

    # ── Recommendation / novelty knobs ────────────────────────────────────
    # Max recommendations generated in a single batch.
    recommendation_batch_size: int = 5
    # How many past activity-families are considered "recently experienced"
    # for fatigue/variety purposes.
    recent_family_window: int = 10
    # Minimum days before a completed skill can be recommended again.
    skill_recomplete_cooldown_days: int = 30

    @field_validator("secret_key")
    @classmethod
    def _secret_key_length(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("secret_key must be at least 32 characters")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()
