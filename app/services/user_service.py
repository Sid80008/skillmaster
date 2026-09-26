"""
User service: registration, authentication, constraint management.
"""
from __future__ import annotations

import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserConstraints
from app.services.exceptions import ConflictError, ForbiddenError, NotFoundError

# ── Registration / Auth ───────────────────────────────────────────────────────


def register_user(
    db: Session,
    *,
    email: str,
    username: str,
    password: str,
) -> User:
    """Create and return a new user account.

    Raises
    ------
    ConflictError
        If the email or username is already taken.
    """
    try:
        user = User(
            email=email.lower().strip(),
            username=username.strip(),
            hashed_password=hash_password(password),
        )
        db.add(user)
        db.flush()  # let the DB catch the UNIQUE constraint before commit
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        raise ConflictError("Email or username already registered.")


def authenticate_user(db: Session, *, email: str, password: str) -> User:
    """Return the user matching *email*+*password* (or username).

    Raises
    ------
    ForbiddenError
        If credentials are wrong or the user is inactive.
    """
    login_identifier = email.strip()
    user = db.query(User).filter(
        (User.email == login_identifier.lower()) | (User.username == login_identifier)
    ).first()
    if user is None or not verify_password(password, user.hashed_password):
        raise ForbiddenError("Incorrect email/username or password.")
    if not user.is_active:
        raise ForbiddenError("Account is deactivated.")
    return user


def create_token_for_user(user: User) -> str:
    """Return a JWT access token for *user*."""
    return create_access_token(subject=str(user.id))


# ── Constraints ───────────────────────────────────────────────────────────────


def get_or_create_constraints(db: Session, *, user: User) -> UserConstraints:
    """Return existing UserConstraints for *user*, creating an empty one if absent."""
    if user.constraints:
        return user.constraints
    constraints = UserConstraints(user_id=user.id)
    db.add(constraints)
    db.commit()
    db.refresh(constraints)
    return constraints


def update_constraints(
    db: Session,
    *,
    user: User,
    physical_restrictions: str | None = None,
    equipment_exclusions: str | None = None,
    max_session_minutes: int | None = None,
) -> UserConstraints:
    """Update or create the user's hard constraints.

    Parameters are merged; passing ``None`` leaves the existing value unchanged.
    Pass an empty string ``""`` to clear a field.
    """
    constraints = get_or_create_constraints(db, user=user)
    if physical_restrictions is not None:
        constraints.physical_restrictions = physical_restrictions or None
    if equipment_exclusions is not None:
        constraints.equipment_exclusions = equipment_exclusions or None
    if max_session_minutes is not None:
        constraints.max_session_minutes = max_session_minutes
    db.commit()
    db.refresh(constraints)
    return constraints


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User:
    """Return the user with *user_id* or raise NotFoundError."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} not found.")
    return user
