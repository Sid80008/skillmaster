"""
Pydantic schemas for Quest and QuestAttempt endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class QuestResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    title: str
    description: str | None
    goal: str | None
    is_active: bool
    catalog_version: int
    created_at: datetime

    model_config = {"from_attributes": True}


class QuestAttemptResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    quest_id: uuid.UUID
    skill_id: uuid.UUID
    skill_name: str | None = None
    activity_family_name: str | None = None
    skill_catalog_version: int
    activity_family_id: uuid.UUID
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    abandoned_at: datetime | None
    abandonment_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AbandonAttemptRequest(BaseModel):
    reason: str | None = Field(
        default=None, max_length=1000, description="Optional reason for abandonment."
    )
