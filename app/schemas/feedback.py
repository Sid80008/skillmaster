"""
Pydantic schemas for Feedback endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class FeedbackSubmitRequest(BaseModel):
    rating: int = Field(ge=1, le=5, description="1–5 star rating.")
    enjoyment_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Normalised enjoyment 0.0–1.0."
    )
    notes: str | None = Field(default=None, max_length=2000)
    tags: str | None = Field(
        default=None,
        max_length=500,
        description="Comma-separated structured tags, e.g. 'too_easy,loved_it'",
    )
    would_repeat: bool | None = None


class FeedbackResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    quest_attempt_id: uuid.UUID
    rating: int
    enjoyment_score: Decimal | None
    notes: str | None
    tags: str | None
    would_repeat: bool | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
