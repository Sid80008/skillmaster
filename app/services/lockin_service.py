"""
Lock-In service.
"""
import uuid
from datetime import datetime, UTC

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from app.models.lockin import LockInSession
from app.models.user import User
from app.models.catalog import Skill
from app.services.exceptions import ConflictError, NotFoundError

def activate_lockin(db: Session, user: User, skill_id: uuid.UUID) -> LockInSession:
    # Check if already locked in
    existing = db.execute(
        select(LockInSession).where(
            and_(
                LockInSession.user_id == user.id,
                LockInSession.status == "active"
            )
        )
    ).scalar_one_or_none()
    
    if existing:
        raise ConflictError("User already has an active lock-in session.")
        
    skill = db.get(Skill, skill_id)
    if not skill or not skill.is_active:
        raise NotFoundError("Skill not found or inactive.")
        
    session = LockInSession(
        user_id=user.id,
        skill_id=skill.id,
        status="active",
        progression_level=0,
    )
    db.add(session)
    
    user.exploration_mode = "locked"
    db.commit()
    db.refresh(session)
    return session

def get_current_lockin(db: Session, user: User) -> LockInSession | None:
    return db.execute(
        select(LockInSession).where(
            and_(
                LockInSession.user_id == user.id,
                LockInSession.status == "active"
            )
        )
    ).scalar_one_or_none()

def exit_lockin(db: Session, user: User, reason: str | None = None) -> LockInSession:
    session = get_current_lockin(db, user)
    if not session:
        raise ConflictError("No active lock-in session to exit.")
        
    session.status = "unlocked"
    session.ended_at = datetime.now(UTC)
    session.unlock_reason = reason
    user.exploration_mode = "explore"
    
    db.commit()
    db.refresh(session)
    return session
