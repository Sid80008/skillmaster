"""
Deterministic novelty engine.

Novelty is calculated from historical state and canonical catalog
relationships — NEVER from AI opinion.

The engine assigns exactly one NoveltyCategory to a (user, skill) pair.

Priority order (highest specificity first)
------------------------------------------
1. EXACT_REPETITION    – skill was attempted before
2. NEAR_DUPLICATE      – skill has a near_duplicate relationship with an
                         already-experienced skill
3. SAME_FAMILY         – skill shares an activity family with experienced skills
4. RELATED_TERRITORY   – skill is in a different family but same category,
                         OR has a complementary/progression relationship
                         with an experienced skill
5. NEW_TERRITORY       – skill is in a family not experienced but in a
                         category the user has visited
6. UNEXPLORED_TERRITORY – skill is in a completely unexplored category

Design principle
----------------
> Affinity can help search farther outward, but affinity can never justify
> remaining inside an already-explored experiential neighborhood.

The novelty category is used as a hard gate: categories EXACT_REPETITION
and NEAR_DUPLICATE are ineligible for new recommendations unless the
cooling-off period has passed (managed by the recommendation service).
"""
from __future__ import annotations

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.catalog import Skill, SkillRelationship
from app.models.recommendation import NoveltyCategory
from app.services.history_service import ExplorationSummary


def classify_novelty(
    skill: Skill,
    summary: ExplorationSummary,
    db: Session,
) -> NoveltyCategory:
    """
    Assign a deterministic NoveltyCategory to *skill* for a user described by
    *summary*.

    Parameters
    ----------
    skill:
        The candidate skill to classify.
    summary:
        The user's exploration summary from ``history_service``.
    db:
        Database session (used only for relationship lookups).
    """
    skill_id = skill.id
    family_id = skill.activity_family_id

    # ── 1. Exact repetition ────────────────────────────────────────────────
    if skill_id in summary.meaningfully_experienced_skill_ids:
        return NoveltyCategory.EXACT_REPETITION

    # ── 2. Near duplicate ─────────────────────────────────────────────────
    # Check if this skill has a near_duplicate relationship with any
    # skill the user has meaningfully experienced.
    if summary.meaningfully_experienced_skill_ids:
        near_dup = db.execute(
            select(SkillRelationship.id).where(
                and_(
                    SkillRelationship.relationship_type == "near_duplicate",
                    SkillRelationship.from_skill_id == skill_id,
                    SkillRelationship.to_skill_id.in_(
                        summary.meaningfully_experienced_skill_ids
                    ),
                )
            ).limit(1)
        ).scalar_one_or_none()
        if near_dup is None:
            # Check reverse direction too (symmetric relationship)
            near_dup = db.execute(
                select(SkillRelationship.id).where(
                    and_(
                        SkillRelationship.relationship_type == "near_duplicate",
                        SkillRelationship.to_skill_id == skill_id,
                        SkillRelationship.from_skill_id.in_(
                            summary.meaningfully_experienced_skill_ids
                        ),
                    )
                ).limit(1)
            ).scalar_one_or_none()
        if near_dup is not None:
            return NoveltyCategory.NEAR_DUPLICATE

    # ── 3. Same family ────────────────────────────────────────────────────
    if family_id in summary.experienced_family_ids:
        return NoveltyCategory.SAME_FAMILY

    # ── 4. Related territory ──────────────────────────────────────────────
    # (a) Same category as an experienced family
    # We need the skill's category ID — go through the activity family.
    skill_category_id = skill.activity_family.category_id if skill.activity_family else None
    if skill_category_id and skill_category_id in summary.experienced_category_ids:
        return NoveltyCategory.RELATED_TERRITORY

    # (b) Has complementary or progression relationship with experienced skills
    if summary.meaningfully_experienced_skill_ids:
        related = db.execute(
            select(SkillRelationship.id).where(
                and_(
                    SkillRelationship.relationship_type.in_(
                        ["complementary", "progression"]
                    ),
                    SkillRelationship.from_skill_id == skill_id,
                    SkillRelationship.to_skill_id.in_(
                        summary.meaningfully_experienced_skill_ids
                    ),
                )
            ).limit(1)
        ).scalar_one_or_none()
        if related is None:
            related = db.execute(
                select(SkillRelationship.id).where(
                    and_(
                        SkillRelationship.relationship_type.in_(
                            ["complementary", "progression"]
                        ),
                        SkillRelationship.to_skill_id == skill_id,
                        SkillRelationship.from_skill_id.in_(
                            summary.meaningfully_experienced_skill_ids
                        ),
                    )
                ).limit(1)
            ).scalar_one_or_none()
        if related is not None:
            return NoveltyCategory.RELATED_TERRITORY

    # ── 5. New territory ──────────────────────────────────────────────────
    if skill_category_id and skill_category_id not in summary.experienced_category_ids:
        if summary.experienced_category_ids:
            # User has explored other categories, but not this one
            return NoveltyCategory.NEW_TERRITORY

    # ── 6. Unexplored territory ───────────────────────────────────────────
    return NoveltyCategory.UNEXPLORED_TERRITORY


# ── Eligibility gates ─────────────────────────────────────────────────────────

# Categories that make a skill ineligible for recommendation
# (without cooldown override).
INELIGIBLE_NOVELTY_CATEGORIES = frozenset(
    {
        NoveltyCategory.EXACT_REPETITION,
        NoveltyCategory.NEAR_DUPLICATE,
    }
)

# Categories that are fully eligible for recommendation
ELIGIBLE_NOVELTY_CATEGORIES = frozenset(
    {
        NoveltyCategory.SAME_FAMILY,
        NoveltyCategory.RELATED_TERRITORY,
        NoveltyCategory.NEW_TERRITORY,
        NoveltyCategory.UNEXPLORED_TERRITORY,
    }
)


def is_novelty_eligible(category: NoveltyCategory) -> bool:
    """Return True if a skill with this novelty category may be recommended."""
    return category in ELIGIBLE_NOVELTY_CATEGORIES


def novelty_score(category: NoveltyCategory) -> float:
    """
    Return a simple deterministic novelty score 0.0–1.0.

    Higher = more novel.  Used for ranking within eligible candidates.
    AI affinity scores may adjust ranking within this framework but
    cannot change category or override ineligibility.
    """
    _scores = {
        NoveltyCategory.UNEXPLORED_TERRITORY: 1.0,
        NoveltyCategory.NEW_TERRITORY: 0.85,
        NoveltyCategory.RELATED_TERRITORY: 0.65,
        NoveltyCategory.SAME_FAMILY: 0.40,
        NoveltyCategory.NEAR_DUPLICATE: 0.10,
        NoveltyCategory.EXACT_REPETITION: 0.0,
    }
    return _scores.get(category, 0.0)
