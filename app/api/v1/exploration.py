"""
Exploration state API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.catalog import Category
from app.services.history_service import get_exploration_summary
from app.schemas.exploration import ExplorationStateResponse

router = APIRouter(prefix="/exploration", tags=["exploration"])


@router.get(
    "/",
    response_model=ExplorationStateResponse,
    summary="Get user's current exploration state",
)
def get_exploration_state(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    summary = get_exploration_summary(db, user_id=current_user.id)
    
    # Calculate unexplored categories
    all_cats = db.execute(select(Category)).scalars().all()
    # Note: family -> category mapping is needed here. The summary gives us families.
    from app.models.catalog import ActivityFamily
    explored_families = db.execute(
        select(ActivityFamily).where(ActivityFamily.id.in_(summary.experienced_family_ids))
    ).scalars().all()
    explored_cat_ids = {f.category_id for f in explored_families}
    
    unexplored_categories = [
        c.name for c in all_cats if c.id not in explored_cat_ids
    ]
    
    from app.models.quest import QuestAttempt, QuestAttemptStatus
    # Count abandoned and completed natively
    all_attempts = db.execute(
        select(QuestAttempt.status)
        .where(QuestAttempt.user_id == current_user.id)
        .where(QuestAttempt.status.in_([QuestAttemptStatus.COMPLETED.value, QuestAttemptStatus.ABANDONED.value]))
    ).scalars().all()
    
    total_completed = sum(1 for s in all_attempts if s == QuestAttemptStatus.COMPLETED.value)
    total_abandoned = sum(1 for s in all_attempts if s == QuestAttemptStatus.ABANDONED.value)

    return ExplorationStateResponse(
        total_completed=total_completed,
        total_abandoned=total_abandoned,
        explored_families_count=len(summary.experienced_family_ids),
        unexplored_categories=unexplored_categories,
        current_exploration_mode=current_user.exploration_mode,
        is_locked_in=current_user.is_locked_in,
    )
