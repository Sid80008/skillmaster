"""
Recommendation endpoints.

POST /api/v1/recommendations/              – generate a new recommendation
GET  /api/v1/recommendations/              – list recommendation history
GET  /api/v1/recommendations/{id}          – get a specific recommendation
POST /api/v1/recommendations/{id}/present  – mark as presented
POST /api/v1/recommendations/{id}/accept   – accept and start a quest attempt
POST /api/v1/recommendations/{id}/reject   – reject
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.recommendation import (
    AcceptRecommendationRequest,
    RejectRecommendationRequest,
    RecommendationResponse,
)
from app.schemas.quest import QuestAttemptResponse
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.services.history_service import get_recommendation_history
from app.services.recommendation_service import (
    accept_recommendation,
    create_recommendation,
    present_recommendation,
    reject_recommendation,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post(
    "/",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new recommendation for the authenticated user",
)
def generate_recommendation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return create_recommendation(db, user=current_user)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/",
    response_model=list[RecommendationResponse],
    summary="List recent recommendations for the authenticated user",
)
def list_recommendations(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return get_recommendation_history(db, user_id=current_user.id, limit=min(limit, 100))


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Get a specific recommendation",
)
def get_recommendation(
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    from app.models.recommendation import Recommendation

    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recommendation not found.")
    if rec.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return rec


@router.post(
    "/{recommendation_id}/present",
    response_model=RecommendationResponse,
    summary="Mark a recommendation as presented to the user",
)
def mark_presented(
    recommendation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return present_recommendation(db, recommendation_id=recommendation_id, user=current_user)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{recommendation_id}/accept",
    response_model=QuestAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept a recommendation and create a QuestAttempt",
)
def accept(
    recommendation_id: uuid.UUID,
    body: AcceptRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        _, attempt = accept_recommendation(
            db,
            recommendation_id=recommendation_id,
            selected_skill_id=body.selected_skill_id,
            user=current_user,
        )
        return attempt
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except (InvalidTransitionError, ConflictError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/{recommendation_id}/reject",
    response_model=RecommendationResponse,
    summary="Reject a recommendation",
)
def reject(
    recommendation_id: uuid.UUID,
    body: RejectRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return reject_recommendation(
            db,
            recommendation_id=recommendation_id,
            reason=body.reason,
            user=current_user,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ForbiddenError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except InvalidTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
