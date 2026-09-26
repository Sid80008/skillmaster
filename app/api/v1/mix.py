"""
Mix API.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.lockin import MixCandidate
from app.models.user import User
from app.schemas.mix import MixCandidateResponse
from app.services.mix_service import discover_mix_candidates

router = APIRouter(prefix="/mix", tags=["mix"])


@router.get(
    "/candidates",
    response_model=list[MixCandidateResponse],
    summary="Get detected Mix Mode candidates for the user",
)
def get_mix_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    if not current_user.mix_mode_enabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mix mode is not enabled.")
        
    # Trigger discovery (idempotent, safe to call on GET for discovery phase)
    new_mixes = discover_mix_candidates(db, current_user)
    
    # Retrieve all unpresented
    candidates = (
        db.execute(
            select(MixCandidate)
            .where(
                and_(
                    MixCandidate.user_id == current_user.id,
                    MixCandidate.is_presented == False,
                )
            )
        )
        .scalars()
        .all()
    )
    return candidates
