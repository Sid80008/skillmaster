"""
Quest attempt endpoints.

GET  /api/v1/quests/attempts/               – list user's attempts
GET  /api/v1/quests/attempts/{id}           – get a specific attempt
POST /api/v1/quests/attempts/{id}/start     – transition PENDING → ACTIVE
POST /api/v1/quests/attempts/{id}/complete  – transition ACTIVE → COMPLETED
POST /api/v1/quests/attempts/{id}/abandon   – transition ACTIVE → ABANDONED
GET  /api/v1/quests/attempts/{id}/feedback  – get feedback for an attempt
POST /api/v1/quests/attempts/{id}/feedback  – submit feedback
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.quest import QuestAttempt, QuestAttemptStatus
from app.models.user import User
from app.schemas.feedback import FeedbackResponse, FeedbackSubmitRequest
from app.schemas.quest import AbandonAttemptRequest, QuestAttemptResponse
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    ValidationError,
)
from app.services.feedback_service import get_feedback_for_attempt, submit_feedback
from app.services.recommendation_service import (
    abandon_quest_attempt,
    complete_quest_attempt,
    start_quest_attempt,
)

router = APIRouter(prefix="/quests", tags=["quests"])


@router.get(
    "/attempts/",
    response_model=list[QuestAttemptResponse],
    summary="List all quest attempts for the authenticated user",
)
def list_attempts(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    attempts = (
        db.execute(
            select(QuestAttempt)
            .where(
                and_(
                    QuestAttempt.user_id == current_user.id,
                    QuestAttempt.status != QuestAttemptStatus.CANCELLED.value,
                )
            )
            .order_by(QuestAttempt.created_at.desc())
            .limit(min(limit, 100))
        )
        .scalars()
        .all()
    )
    return attempts


@router.get(
    "/attempts/{attempt_id}",
    response_model=QuestAttemptResponse,
    summary="Get a specific quest attempt",
)
def get_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    attempt = db.get(QuestAttempt, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QuestAttempt not found.")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return attempt


@router.post(
    "/attempts/{attempt_id}/start",
    response_model=QuestAttemptResponse,
    summary="Start a quest attempt (PENDING → ACTIVE)",
)
def start_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return start_quest_attempt(db, attempt_id=attempt_id, user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/attempts/{attempt_id}/complete",
    response_model=QuestAttemptResponse,
    summary="Complete a quest attempt (ACTIVE → COMPLETED)",
)
def complete_attempt(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return complete_quest_attempt(db, attempt_id=attempt_id, user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/attempts/{attempt_id}/abandon",
    response_model=QuestAttemptResponse,
    summary="Abandon a quest attempt (ACTIVE → ABANDONED)",
)
def abandon_attempt(
    attempt_id: uuid.UUID,
    body: AbandonAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return abandon_quest_attempt(db, attempt_id=attempt_id, reason=body.reason, user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/attempts/{attempt_id}/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback for a completed or abandoned quest attempt",
)
def post_feedback(
    attempt_id: uuid.UUID,
    body: FeedbackSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return submit_feedback(
            db,
            user=current_user,
            quest_attempt_id=attempt_id,
            rating=body.rating,
            enjoyment_score=body.enjoyment_score,
            notes=body.notes,
            tags=body.tags,
            would_repeat=body.would_repeat,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except (ValidationError, ConflictError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/attempts/{attempt_id}/feedback",
    response_model=FeedbackResponse | None,
    summary="Get feedback for a quest attempt",
)
def get_attempt_feedback(
    attempt_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return get_feedback_for_attempt(db, quest_attempt_id=attempt_id, user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
