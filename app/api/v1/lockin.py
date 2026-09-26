"""
Lock-In API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.lockin import LockInActivateRequest, LockInSessionResponse
from app.services.exceptions import ConflictError, NotFoundError
from app.services.lockin_service import activate_lockin, exit_lockin, get_current_lockin

router = APIRouter(prefix="/lock-in", tags=["lock-in"])

class ExitRequest(BaseModel):
    reason: str | None = None

@router.post(
    "/activate",
    response_model=LockInSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Activate Lock-In mode for a specific skill",
)
def activate(
    body: LockInActivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return activate_lockin(db, current_user, body.skill_id)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/current",
    response_model=LockInSessionResponse | None,
    summary="Get current active Lock-In session",
)
def get_current(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return get_current_lockin(db, current_user)


@router.post(
    "/exit",
    response_model=LockInSessionResponse,
    summary="Exit Lock-In mode",
)
def exit_mode(
    body: ExitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    try:
        return exit_lockin(db, current_user, body.reason)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
