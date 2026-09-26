"""
Mix Mode service.

Detects strong intersecting interests and creates MixCandidate recommendations.
"""
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.catalog import Skill
from app.models.lockin import MixCandidate
from app.models.rating import Rating
from app.models.user import User


def discover_mix_candidates(db: Session, user: User) -> list[MixCandidate]:
    """
    Look for pairs of highly-rated skills that the user has experienced,
    and see if there's a third unexplored skill that combines their tags
    or belongs to a related cross-disciplinary category.
    
    (Simplified deterministic version)
    """
    if not user.mix_mode_enabled:
        return []
        
    # Get user's high-rated skills
    high_ratings = (
        db.execute(
            select(Rating)
            .where(Rating.user_id == user.id)
            .where(Rating.enjoyment >= user.mix_threshold)
        )
        .scalars()
        .all()
    )
    
    if len(high_ratings) < 2:
        return []
        
    high_skill_ids = {r.skill_id for r in high_ratings}
    skills = db.execute(select(Skill).where(Skill.id.in_(high_skill_ids))).scalars().all()
    
    new_candidates = []
    
    # Simple combinatorial pass: look for intersection of characteristic tags
    # For a real production app, this would use an LLM or pre-computed embeddings.
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            skill_a = skills[i]
            skill_b = skills[j]
            
            # Avoid mixing skills from the same family
            if skill_a.activity_family_id == skill_b.activity_family_id:
                continue
                
            # Check if this pair was already mixed
            existing = db.execute(
                select(MixCandidate).where(
                    and_(
                        MixCandidate.user_id == user.id,
                        MixCandidate.skill_a_id == skill_a.id,
                        MixCandidate.skill_b_id == skill_b.id,
                    )
                )
            ).scalar_one_or_none()
            
            if existing:
                continue
                
            # If both have tags, find a third unplayed skill that shares tags from both
            if skill_a.characteristic_tags and skill_b.characteristic_tags:
                tags_a = set(skill_a.characteristic_tags.split(","))
                tags_b = set(skill_b.characteristic_tags.split(","))
                
                # We want a skill that has at least one tag from A and one from B
                # (Simplified heuristic)
                all_unplayed = db.execute(
                    select(Skill).where(Skill.id.notin_(high_skill_ids))
                ).scalars().all()
                
                for candidate_skill in all_unplayed:
                    if not candidate_skill.characteristic_tags:
                        continue
                    c_tags = set(candidate_skill.characteristic_tags.split(","))
                    if (c_tags & tags_a) and (c_tags & tags_b):
                        # Found a mix
                        mix = MixCandidate(
                            user_id=user.id,
                            skill_a_id=skill_a.id,
                            skill_b_id=skill_b.id,
                            result_skill_id=candidate_skill.id,
                            mix_label=f"{skill_a.name} + {skill_b.name}",
                            mix_explanation=f"Combines elements of {skill_a.name} and {skill_b.name}.",
                            confidence=Decimal("0.850"),
                        )
                        db.add(mix)
                        new_candidates.append(mix)
                        break
                        
    if new_candidates:
        db.commit()
        
    return new_candidates
