"""
Authentication and user management endpoints.

POST /api/v1/auth/register  – create a new account
POST /api/v1/auth/token     – log in, get a JWT
GET  /api/v1/auth/me        – return the authenticated user
PUT  /api/v1/auth/constraints – update the user's hard constraints
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.user import (
    ConstraintsRequest,
    ConstraintsResponse,
    TokenResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.services.exceptions import ConflictError, ForbiddenError
from app.services.user_service import (
    authenticate_user,
    create_token_for_user,
    get_or_create_constraints,
    register_user,
    update_constraints,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    body: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> User:
    try:
        return register_user(db, email=body.email, username=body.username, password=body.password)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT access token",
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    try:
        user = authenticate_user(db, email=form_data.username, password=form_data.password)
    except ForbiddenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return {"access_token": create_token_for_user(user), "token_type": "bearer"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the authenticated user's profile",
)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put(
    "/constraints",
    response_model=ConstraintsResponse,
    summary="Update (or create) the user's hard eligibility constraints",
)
def update_user_constraints(
    body: ConstraintsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return update_constraints(
        db,
        user=current_user,
        physical_restrictions=body.physical_restrictions,
        equipment_exclusions=body.equipment_exclusions,
        max_session_minutes=body.max_session_minutes,
    )


@router.get(
    "/constraints",
    response_model=ConstraintsResponse,
    summary="Retrieve the user's current constraints",
)
def get_user_constraints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    return get_or_create_constraints(db, user=current_user)
