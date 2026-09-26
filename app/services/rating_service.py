"""
Rating and DNA service.

Processes post-experience ratings, computes composite scores, and updates
the user's Skill DNA and Category Profiles.
"""
import uuid
from decimal import Decimal
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rating import Rating
from app.models.quest import QuestAttempt
from app.models.dna import SkillDNA, UserCategoryProfile
from app.models.catalog import Skill, Category, ActivityFamily
from app.models.user import User
from app.services.exceptions import NotFoundError, ConflictError


def _compute_composite_score(r: Rating) -> Decimal:
    """
    Computes a 0.0-1.0 composite signal from a rating.
    Weights (simplified):
      Enjoyment: 40%
      Curiosity: 30%
      Deep Dive: 15%
      Repeat: 15% (yes=1.0, maybe=0.5, no=0.0)
    """
    repeat_val = 1.0 if r.would_repeat == "yes" else (0.5 if r.would_repeat == "maybe" else 0.0)
    
    enjoyment_norm = r.enjoyment / 10.0
    curiosity_norm = r.curiosity / 10.0
    deep_dive_norm = r.deep_dive_interest / 10.0
    
    score = (
        (enjoyment_norm * 0.40) +
        (curiosity_norm * 0.30) +
        (deep_dive_norm * 0.15) +
        (repeat_val * 0.15)
    )
    return Decimal(str(round(score, 4)))


def submit_rating(
    db: Session,
    user: User,
    attempt_id: uuid.UUID,
    enjoyment: int,
    curiosity: int,
    would_repeat: str,
    deep_dive_interest: int,
    pre_interest: int | None = None,
    difficulty_felt: int | None = None,
    standout_moment: str | None = None,
    friction_notes: str | None = None,
) -> Rating:
    """Submit a rating for an attempt, and update DNA/Profiles."""
    
    # 1. Validate attempt
    attempt = db.query(QuestAttempt).filter_by(id=attempt_id, user_id=user.id).first()
    if not attempt:
        raise NotFoundError("Quest attempt not found.")
    if attempt.status not in ("completed", "abandoned"):
        raise ConflictError("Can only rate completed or abandoned attempts.")
        
    # Check for existing rating
    existing = db.query(Rating).filter_by(quest_attempt_id=attempt.id).first()
    if existing:
        raise ConflictError("Rating already submitted for this attempt.")
        
    # 2. Create rating
    rating = Rating(
        user_id=user.id,
        quest_attempt_id=attempt.id,
        skill_id=attempt.skill_id,
        challenge_id=attempt.challenge_id,
        enjoyment=enjoyment,
        curiosity=curiosity,
        would_repeat=would_repeat.lower(),
        deep_dive_interest=deep_dive_interest,
        pre_interest=pre_interest,
        difficulty_felt=difficulty_felt,
        standout_moment=standout_moment,
        friction_notes=friction_notes,
    )
    
    # 3. Compute score
    score = _compute_composite_score(rating)
    rating.composite_score = score
    rating.affinity_signal = score  # For now, 1:1
    
    db.add(rating)
    
    # 4. Update UserCategoryProfile
    skill = attempt.skill
    family = skill.activity_family
    cat_id = family.category_id
    
    ucp = db.query(UserCategoryProfile).filter_by(user_id=user.id, category_id=cat_id).first()
    if not ucp:
        ucp = UserCategoryProfile(
            user_id=user.id, 
            category_id=cat_id, 
            exposure_count=0,
            affinity_score=Decimal("0.5000"),
            fatigue_level=Decimal("0.0000")
        )
        db.add(ucp)
        
    # EMA update for affinity
    old_affinity = float(ucp.affinity_score)
    new_affinity = (old_affinity * 0.7) + (float(score) * 0.3)
    
    ucp.exposure_count += 1
    ucp.affinity_score = Decimal(str(round(new_affinity, 4)))
    # Increase fatigue by 0.2, max 1.0 (will decay elsewhere)
    ucp.fatigue_level = min(Decimal("1.0"), ucp.fatigue_level + Decimal("0.2"))
    
    # 5. Update SkillDNA
    if skill.characteristic_tags:
        tags = [t.strip() for t in skill.characteristic_tags.split(",") if t.strip()]
        for tag in tags:
            dna = db.query(SkillDNA).filter_by(user_id=user.id, characteristic_slug=tag).first()
            if not dna:
                dna = SkillDNA(
                    user_id=user.id, 
                    characteristic_slug=tag,
                    sample_count=0,
                    confidence=Decimal("0.000"),
                    affinity_value=Decimal("0.5000"),
                )
                db.add(dna)
            
            dna.sample_count += 1
            # Adjust confidence: 0.1 per sample up to 1.0
            dna.confidence = min(Decimal("1.0"), Decimal(str(dna.sample_count * 0.1)))
            
            # Simple EMA for affinity
            old_val = float(dna.affinity_value)
            new_val = (old_val * 0.8) + (float(score) * 0.2)
            dna.affinity_value = Decimal(str(round(new_val, 4)))
            
    db.flush()
    return rating
