"""
Pydantic schemas for Recommendation endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RecommendationCandidateResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    skill_catalog_version: int
    rank: int
    score: Decimal
    novelty_category: str
    explanation: str | None

    model_config = {"from_attributes": True}


class RecommendationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    presented_at: datetime | None
    responded_at: datetime | None
    selected_skill_id: uuid.UUID | None
    resulting_quest_attempt_id: uuid.UUID | None
    generation_context: str | None
    rejection_reason: str | None
    candidates: list[RecommendationCandidateResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AcceptRecommendationRequest(BaseModel):
    selected_skill_id: uuid.UUID = Field(
        description="The skill UUID from the recommendation's candidate list that the user is accepting."
    )


class RejectRecommendationRequest(BaseModel):
    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional reason for rejection.",
    )
