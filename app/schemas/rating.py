import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class RatingSubmitRequest(BaseModel):
    pre_interest: int | None = Field(default=None, ge=1, le=10)
    enjoyment: int = Field(..., ge=1, le=10)
    curiosity: int = Field(..., ge=1, le=10)
    difficulty_felt: int | None = Field(default=None, ge=1, le=10)
    would_repeat: Literal["yes", "maybe", "no"]
    deep_dive_interest: int = Field(..., ge=1, le=10)
    standout_moment: str | None = Field(default=None, max_length=2000)
    friction_notes: str | None = Field(default=None, max_length=2000)
    free_text: str | None = Field(default=None, max_length=2000)

class RatingResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    quest_attempt_id: uuid.UUID
    skill_id: uuid.UUID
    enjoyment: int
    curiosity: int
    deep_dive_interest: int
    would_repeat: str
    composite_score: Decimal | None
    created_at: datetime
    
    model_config = {"from_attributes": True}
