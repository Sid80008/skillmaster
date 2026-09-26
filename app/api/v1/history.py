"""
Exploration history endpoints.

GET /api/v1/history/summary   – full exploration summary for the current user
GET /api/v1/history/attempts  – recent quest attempts
GET /api/v1/history/recommendations – recent recommendation history
"""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.quest import QuestAttemptResponse
from app.schemas.recommendation import RecommendationResponse
from app.services.history_service import (
    get_exploration_summary,
    get_recent_attempts,
    get_recommendation_history,
)

router = APIRouter(prefix="/history", tags=["history"])


class ExplorationSummaryResponse(BaseModel):
    attempted_skill_count: int
    completed_skill_count: int
    meaningfully_experienced_skill_count: int
    experienced_family_count: int
    experienced_category_count: int
    attempted_skill_ids: list[uuid.UUID]
    completed_skill_ids: list[uuid.UUID]
    experienced_family_ids: list[uuid.UUID]


@router.get(
    "/summary",
    response_model=ExplorationSummaryResponse,
    summary="Return the user's full exploration summary (computed from QuestAttempts)",
)
def exploration_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ExplorationSummaryResponse:
    summary = get_exploration_summary(db, user_id=current_user.id)
    return ExplorationSummaryResponse(
        attempted_skill_count=len(summary.attempted_skill_ids),
        completed_skill_count=len(summary.completed_skill_ids),
        meaningfully_experienced_skill_count=len(summary.meaningfully_experienced_skill_ids),
        experienced_family_count=len(summary.experienced_family_ids),
        experienced_category_count=len(summary.experienced_category_ids),
        attempted_skill_ids=list(summary.attempted_skill_ids),
        completed_skill_ids=list(summary.completed_skill_ids),
        experienced_family_ids=list(summary.experienced_family_ids),
    )


@router.get(
    "/attempts",
    response_model=list[QuestAttemptResponse],
    summary="Return recent quest attempts for the user",
)
def recent_attempts(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return get_recent_attempts(db, user_id=current_user.id, limit=min(limit, 100))


@router.get(
    "/recommendations",
    response_model=list[RecommendationResponse],
    summary="Return recent recommendation history for the user",
)
def recent_recommendations(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return get_recommendation_history(db, user_id=current_user.id, limit=min(limit, 100))
