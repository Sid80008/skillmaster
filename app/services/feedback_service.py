"""
Feedback service.

Ownership + eligibility rules enforced here:
- The QuestAttempt must belong to the authenticated user.
- The QuestAttempt must be in COMPLETED or ABANDONED status.
- Each attempt can only have one Feedback (DB unique constraint + service guard).
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.feedback import Feedback
from app.models.quest import QuestAttempt, QuestAttemptStatus
from app.models.user import User
from app.services.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError


def submit_feedback(
    db: Session,
    *,
    user: User,
    quest_attempt_id: uuid.UUID,
    rating: int,
    enjoyment_score: float | None = None,
    notes: str | None = None,
    tags: str | None = None,
    would_repeat: bool | None = None,
) -> Feedback:
    """
    Create a Feedback record for a completed or abandoned quest attempt.

    Raises
    ------
    NotFoundError
        If the QuestAttempt doesn't exist.
    ForbiddenError
        If the attempt doesn't belong to the authenticated user.
    ValidationError
        If the attempt status doesn't allow feedback.
    ConflictError
        If feedback already exists for this attempt.
    """
    attempt = db.get(QuestAttempt, quest_attempt_id)
    if attempt is None:
        raise NotFoundError(f"QuestAttempt {quest_attempt_id} not found.")
    if attempt.user_id != user.id:
        raise ForbiddenError("You do not own this quest attempt.")

    # Only completed or abandoned attempts can receive feedback
    if attempt.status not in (
        QuestAttemptStatus.COMPLETED.value,
        QuestAttemptStatus.ABANDONED.value,
    ):
        raise ValidationError(
            f"Cannot submit feedback for a quest attempt in status {attempt.status!r}. "
            "Only COMPLETED or ABANDONED attempts accept feedback."
        )

    # Guard: one feedback per attempt
    existing = db.execute(
        select(Feedback.id).where(
            Feedback.quest_attempt_id == quest_attempt_id
        ).limit(1)
    ).scalar_one_or_none()
    if existing is not None:
        raise ConflictError(
            f"Feedback already exists for quest attempt {quest_attempt_id}."
        )

    if not (1 <= rating <= 5):
        raise ValidationError("Rating must be between 1 and 5.")
    if enjoyment_score is not None and not (0.0 <= enjoyment_score <= 1.0):
        raise ValidationError("enjoyment_score must be between 0.0 and 1.0.")

    try:
        feedback = Feedback(
            user_id=user.id,
            quest_attempt_id=quest_attempt_id,
            rating=rating,
            enjoyment_score=Decimal(str(enjoyment_score)) if enjoyment_score is not None else None,
            notes=notes,
            tags=tags,
            would_repeat=would_repeat,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return feedback
    except IntegrityError:
        db.rollback()
        raise ConflictError(
            f"Feedback already exists for quest attempt {quest_attempt_id}."
        )


def get_feedback(
    db: Session, *, feedback_id: uuid.UUID, user: User
) -> Feedback:
    """Return a Feedback by ID, enforcing ownership."""
    feedback = db.get(Feedback, feedback_id)
    if feedback is None:
        raise NotFoundError(f"Feedback {feedback_id} not found.")
    if feedback.user_id != user.id:
        raise ForbiddenError("You do not own this feedback.")
    return feedback


def get_feedback_for_attempt(
    db: Session, *, quest_attempt_id: uuid.UUID, user: User
) -> Feedback | None:
    """Return the Feedback for a given attempt, or None if not submitted yet."""
    attempt = db.get(QuestAttempt, quest_attempt_id)
    if attempt is None:
        raise NotFoundError(f"QuestAttempt {quest_attempt_id} not found.")
    if attempt.user_id != user.id:
        raise ForbiddenError("You do not own this quest attempt.")
    return db.execute(
        select(Feedback).where(Feedback.quest_attempt_id == quest_attempt_id)
    ).scalar_one_or_none()
