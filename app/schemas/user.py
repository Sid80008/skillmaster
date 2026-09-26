"""
Pydantic schemas for User and auth endpoints.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def _username_chars(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-zA-Z0-9_.-]+$", v):
            raise ValueError(
                "Username may only contain letters, digits, underscores, dots, and hyphens."
            )
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ConstraintsRequest(BaseModel):
    physical_restrictions: str | None = Field(
        default=None,
        description=(
            "Comma-separated constraint tags. "
            "Pass empty string to clear. Example: 'no_high_impact,no_overhead_reach'"
        ),
    )
    equipment_exclusions: str | None = Field(
        default=None,
        description=(
            "Comma-separated equipment tags the user DOES NOT have. "
            "Example: 'bicycle,climbing_harness'"
        ),
    )
    max_session_minutes: int | None = Field(
        default=None,
        ge=5,
        le=720,
        description="Maximum session length in minutes.",
    )


class ConstraintsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    physical_restrictions: str | None
    equipment_exclusions: str | None
    max_session_minutes: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
