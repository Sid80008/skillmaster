"""
Profile and behavioral APIs.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.dna import SkillDNA, UserCategoryProfile
from app.schemas.profile import SkillDNAResponse, UserCategoryProfileResponse, UserProfileResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get(
    "/",
    response_model=UserProfileResponse,
    summary="Get user's behavioral profile modes",
)
def get_profile(
    current_user: User = Depends(get_current_user),
) -> object:
    return current_user


@router.get(
    "/dna",
    response_model=list[SkillDNAResponse],
    summary="Get user's extracted Skill DNA",
)
def get_dna(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    dna_records = (
        db.execute(select(SkillDNA).where(SkillDNA.user_id == current_user.id))
        .scalars()
        .all()
    )
    return dna_records


@router.get(
    "/categories",
    response_model=list[UserCategoryProfileResponse],
    summary="Get user's category exposure and fatigue statistics",
)
def get_category_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> object:
    cat_profiles = (
        db.execute(select(UserCategoryProfile).where(UserCategoryProfile.user_id == current_user.id))
        .scalars()
        .all()
    )
    return cat_profiles
