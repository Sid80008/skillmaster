"""
Exploration history service.

The authoritative source of truth for a user's exploration history is the
QuestAttempt table — never the user profile or AI-derived DNA.

This service answers the deterministic questions:
- Has this user attempted this skill?
- Has this user completed this skill?
- Has this user meaningfully experienced this skill?
- Which activity families has this user experienced?
- What has the user recently attempted/completed/abandoned?
- What recommendation/quest history exists for this user?
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import NamedTuple

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.quest import QuestAttempt, QuestAttemptStatus
from app.models.recommendation import Recommendation, RecommendationStatus


class ExplorationSummary(NamedTuple):
    """Computed exploration state for a single user."""

    attempted_skill_ids: frozenset[uuid.UUID]
    """Skills attempted at least once (any non-cancelled status)."""

    completed_skill_ids: frozenset[uuid.UUID]
    """Skills completed at least once."""

    meaningfully_experienced_skill_ids: frozenset[uuid.UUID]
    """Skills that are completed OR were actively started (ACTIVE/ABANDONED).
    Pending-only attempts do not count as meaningful experience."""

    experienced_family_ids: frozenset[uuid.UUID]
    """Activity families of all meaningfully experienced skills."""

    experienced_category_ids: frozenset[uuid.UUID]
    """Category IDs derived from experienced families."""


def get_exploration_summary(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> ExplorationSummary:
    """
    Compute the full exploration summary for a user from QuestAttempts.

    This is the single authoritative source — not profile, not DNA.
    """
    # Load all non-cancelled attempts for the user
    attempts = (
        db.execute(
            select(QuestAttempt).where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.status != QuestAttemptStatus.CANCELLED.value,
                )
            )
        )
        .scalars()
        .all()
    )

    attempted_ids: set[uuid.UUID] = set()
    completed_ids: set[uuid.UUID] = set()
    meaningful_ids: set[uuid.UUID] = set()
    family_ids: set[uuid.UUID] = set()

    for attempt in attempts:
        status = QuestAttemptStatus(attempt.status)
        attempted_ids.add(attempt.skill_id)
        if status == QuestAttemptStatus.COMPLETED:
            completed_ids.add(attempt.skill_id)
        # Meaningful = started (active, completed, or abandoned)
        if status in (
            QuestAttemptStatus.ACTIVE,
            QuestAttemptStatus.COMPLETED,
            QuestAttemptStatus.ABANDONED,
        ):
            meaningful_ids.add(attempt.skill_id)
            family_ids.add(attempt.activity_family_id)

    # Derive category IDs from activity families
    category_ids: set[uuid.UUID] = set()
    if family_ids:
        from app.models.catalog import ActivityFamily

        families = (
            db.execute(
                select(ActivityFamily).where(ActivityFamily.id.in_(family_ids))
            )
            .scalars()
            .all()
        )
        category_ids = {f.category_id for f in families}

    return ExplorationSummary(
        attempted_skill_ids=frozenset(attempted_ids),
        completed_skill_ids=frozenset(completed_ids),
        meaningfully_experienced_skill_ids=frozenset(meaningful_ids),
        experienced_family_ids=frozenset(family_ids),
        experienced_category_ids=frozenset(category_ids),
    )


def has_attempted_skill(
    db: Session, *, user_id: uuid.UUID, skill_id: uuid.UUID
) -> bool:
    """Return True if the user has any non-cancelled attempt for this skill."""
    return (
        db.execute(
            select(QuestAttempt.id).where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.skill_id == skill_id,
                    QuestAttempt.status != QuestAttemptStatus.CANCELLED.value,
                )
            ).limit(1)
        ).scalar_one_or_none()
        is not None
    )


def has_completed_skill(
    db: Session, *, user_id: uuid.UUID, skill_id: uuid.UUID
) -> bool:
    """Return True if the user has at least one COMPLETED attempt for this skill."""
    return (
        db.execute(
            select(QuestAttempt.id).where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.skill_id == skill_id,
                    QuestAttempt.status == QuestAttemptStatus.COMPLETED.value,
                )
            ).limit(1)
        ).scalar_one_or_none()
        is not None
    )


def has_meaningfully_experienced_skill(
    db: Session, *, user_id: uuid.UUID, skill_id: uuid.UUID
) -> bool:
    """Return True if the user has started (active, completed, or abandoned) this skill."""
    meaningful_statuses = [
        QuestAttemptStatus.ACTIVE.value,
        QuestAttemptStatus.COMPLETED.value,
        QuestAttemptStatus.ABANDONED.value,
    ]
    return (
        db.execute(
            select(QuestAttempt.id).where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.skill_id == skill_id,
                    QuestAttempt.status.in_(meaningful_statuses),
                )
            ).limit(1)
        ).scalar_one_or_none()
        is not None
    )


def get_recent_attempts(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[QuestAttempt]:
    """Return the N most recent non-cancelled attempts for the user, newest first."""
    return (
        db.execute(
            select(QuestAttempt)
            .where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.status != QuestAttemptStatus.CANCELLED.value,
                )
            )
            .order_by(QuestAttempt.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def get_recent_experienced_family_ids(
    db: Session,
    *,
    user_id: uuid.UUID,
    window: int = 10,
) -> list[uuid.UUID]:
    """
    Return the activity family IDs of the N most recently *started* attempts.

    Used for variety / fatigue calculations in the recommender.
    Order: most recent first (index 0 = most recently experienced).
    """
    recent = (
        db.execute(
            select(QuestAttempt.activity_family_id)
            .where(
                and_(
                    QuestAttempt.user_id == user_id,
                    QuestAttempt.status.in_(
                        [
                            QuestAttemptStatus.ACTIVE.value,
                            QuestAttemptStatus.COMPLETED.value,
                            QuestAttemptStatus.ABANDONED.value,
                        ]
                    ),
                )
            )
            .order_by(QuestAttempt.created_at.desc())
            .limit(window)
        )
        .scalars()
        .all()
    )
    return list(recent)


def get_recommendation_history(
    db: Session,
    *,
    user_id: uuid.UUID,
    limit: int = 20,
) -> list[Recommendation]:
    """Return the N most recent recommendations for the user, newest first."""
    return (
        db.execute(
            select(Recommendation)
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
