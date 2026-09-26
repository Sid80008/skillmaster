"""
Recommendation service.

Pipeline
--------
candidate_generation
    → hard constraint filter
    → novelty eligibility filter
    → fatigue/variety filter
    → ranking
    → Recommendation + RecommendationCandidate creation

Design invariants
-----------------
* AI is advisory only — the pipeline runs fully without it.
* Hard constraints and novelty eligibility gates are never bypassed.
* All state mutations happen inside a single database transaction.
* Duplicate recommendation creation is protected by checking for
  an existing PENDING or PRESENTED recommendation for the user.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.catalog import Skill
from app.models.quest import (
    Quest,
    QuestAttempt,
    QuestAttemptStatus,
)
from app.models.recommendation import (
    NoveltyCategory,
    Recommendation,
    RecommendationCandidate,
    RecommendationStatus,
)
from app.models.user import User
from app.services.constraint_service import check_skill_constraints, filter_eligible_skills
from app.services.exceptions import (
    ConflictError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
)
from app.services.history_service import (
    ExplorationSummary,
    get_exploration_summary,
    get_recent_experienced_family_ids,
)
from app.services.novelty_service import (
    classify_novelty,
    is_novelty_eligible,
    novelty_score,
)

log = get_logger(__name__)


# ── Candidate generation ──────────────────────────────────────────────────────


@dataclass
class ScoredCandidate:
    skill: Skill
    novelty_category: NoveltyCategory
    score: float
    explanation: str


def _generate_candidates(
    db: Session,
    user: User,
    summary: ExplorationSummary,
) -> list[ScoredCandidate]:
    """
    Run the full candidate pipeline and return a ranked list.

    Pipeline steps
    --------------
    1. Load all active catalog skills.
    2. Apply hard constraint filter.
    3. Classify novelty for each candidate.
    4. Apply novelty eligibility filter.
    5. Apply variety filter (reduce family fatigue).
    6. Rank by novelty score (deterministic baseline).
    7. Return top-N.

    AI hook (future)
    ----------------
    After step 6, an AI affinity scoring function may adjust scores within
    each novelty tier.  It must never promote an ineligible skill.
    """
    settings = get_settings()

    # Step 1: load active skills
    all_skills: list[Skill] = (
        db.execute(select(Skill).where(Skill.is_active == True))
        .scalars()
        .all()
    )

    # Step 2: constraint filter
    eligible_skills = filter_eligible_skills(all_skills, user.constraints)

    # Step 3 & 4: novelty classification and eligibility gate
    novelty_classified: list[tuple[Skill, NoveltyCategory]] = []
    for skill in eligible_skills:
        category = classify_novelty(skill, summary, db)
        if is_novelty_eligible(category):
            novelty_classified.append((skill, category))

    # Step 5: variety filter — pull category profiles for fatigue
    from app.models.dna import UserCategoryProfile
    category_profiles = (
        db.execute(select(UserCategoryProfile).where(UserCategoryProfile.user_id == user.id))
        .scalars()
        .all()
    )
    fatigue_map = {cp.category_id: float(cp.fatigue_level) for cp in category_profiles}
    affinity_map = {cp.category_id: float(cp.affinity_score) for cp in category_profiles}

    recent_families = get_recent_experienced_family_ids(
        db, user_id=user.id, window=settings.recent_family_window
    )
    family_fatigue: dict[uuid.UUID, float] = {}
    for idx, fam_id in enumerate(recent_families):
        family_fatigue[fam_id] = 1.0 - (idx / max(len(recent_families), 1))

    # Step 6: score and rank
    scored: list[ScoredCandidate] = []
    for skill, category in novelty_classified:
        base_score = novelty_score(category)
        
        # Category fatigue
        cat_fatigue = fatigue_map.get(skill.activity_family.category_id, 0.0)
        # Family fatigue (from recent window)
        fam_fatigue = family_fatigue.get(skill.activity_family_id, 0.0)
        
        # If user has locked in, we want depth. If explore (default), we penalize fatigue heavily.
        if user.is_locked_in:
            # depth: fatigue is not penalized, maybe even rewarded for the locked skill
            final_score = base_score
            explanation = f"LOCK IN Mode. Novelty: {category.value}."
        else:
            # explore: apply anti-bubble variety
            fatigue_penalty = (fam_fatigue * 0.4) + (cat_fatigue * 0.2)
            final_score = max(0.0, base_score - fatigue_penalty)
            explanation = (
                f"Novelty: {category.value}. "
                f"Base score: {base_score:.2f}. "
                f"Fatigue penalty: {fatigue_penalty:.2f}."
            )
            
        scored.append(
            ScoredCandidate(
                skill=skill,
                novelty_category=category,
                score=final_score,
                explanation=explanation,
            )
        )

    # Sort descending by score, then by skill name for determinism
    scored.sort(key=lambda c: (-c.score, c.skill.name))

    return scored[: settings.recommendation_batch_size]


# ── Recommendation creation ───────────────────────────────────────────────────


def create_recommendation(db: Session, *, user: User) -> Recommendation:
    """
    Generate and persist a new recommendation batch for *user*.

    Raises
    ------
    ConflictError
        If the user already has an open (PENDING or PRESENTED) recommendation.
    NotFoundError
        If no eligible candidates can be found.
    """
    # Duplicate guard: one open recommendation at a time
    existing = db.execute(
        select(Recommendation).where(
            and_(
                Recommendation.user_id == user.id,
                Recommendation.status.in_(
                    [RecommendationStatus.PENDING.value, RecommendationStatus.PRESENTED.value]
                ),
            )
        ).limit(1)
    ).scalar_one_or_none()

    if existing is not None:
        raise ConflictError(
            f"User already has an open recommendation ({existing.id}). "
            "Resolve it before generating a new one."
        )

    # Compute exploration summary
    summary = get_exploration_summary(db, user_id=user.id)

    # Generate candidates
    candidates = _generate_candidates(db, user, summary)
    if not candidates:
        raise NotFoundError(
            "No eligible candidates found. All skills may be constraint-blocked "
            "or already explored."
        )

    # Create the Recommendation row
    recommendation = Recommendation(
        user_id=user.id,
        status=RecommendationStatus.PENDING.value,
        generation_context=(
            f"Generated {datetime.now(UTC).isoformat()}. "
            f"Experienced {len(summary.meaningfully_experienced_skill_ids)} skills, "
            f"{len(summary.experienced_family_ids)} families."
        ),
    )
    db.add(recommendation)
    db.flush()  # get recommendation.id

    # Create candidate rows
    for rank, sc in enumerate(candidates, start=1):
        candidate = RecommendationCandidate(
            recommendation_id=recommendation.id,
            skill_id=sc.skill.id,
            skill_catalog_version=sc.skill.catalog_version,
            rank=rank,
            score=Decimal(str(round(sc.score, 4))),
            novelty_category=sc.novelty_category.value,
            explanation=sc.explanation,
        )
        db.add(candidate)

    db.commit()
    db.refresh(recommendation)
    log.info(
        "recommendation_created",
        recommendation_id=str(recommendation.id),
        user_id=str(user.id),
        candidate_count=len(candidates),
    )
    return recommendation


# ── Recommendation state transitions ──────────────────────────────────────────


def present_recommendation(
    db: Session, *, recommendation_id: uuid.UUID, user: User
) -> Recommendation:
    """Mark the recommendation as PRESENTED to the user."""
    rec = _get_recommendation_for_user(db, recommendation_id=recommendation_id, user=user)
    _assert_transition(rec, RecommendationStatus.PRESENTED)
    rec.status = RecommendationStatus.PRESENTED.value
    rec.presented_at = datetime.now(UTC)
    db.commit()
    db.refresh(rec)
    return rec


def accept_recommendation(
    db: Session,
    *,
    recommendation_id: uuid.UUID,
    selected_skill_id: uuid.UUID,
    user: User,
) -> tuple[Recommendation, QuestAttempt]:
    """
    Accept a recommendation and create the resulting QuestAttempt.

    The selected skill must be one of the recommendation's candidates.
    The resulting QuestAttempt starts in PENDING status.

    Returns
    -------
    (recommendation, quest_attempt)
    """
    rec = _get_recommendation_for_user(db, recommendation_id=recommendation_id, user=user)
    _assert_transition(rec, RecommendationStatus.ACCEPTED)

    # Validate that selected_skill_id is among the candidates
    candidate = db.execute(
        select(RecommendationCandidate).where(
            and_(
                RecommendationCandidate.recommendation_id == rec.id,
                RecommendationCandidate.skill_id == selected_skill_id,
            )
        )
    ).scalar_one_or_none()
    if candidate is None:
        raise NotFoundError(
            f"Skill {selected_skill_id} is not a candidate for recommendation {recommendation_id}."
        )

    # Confirm the skill is still active (catalog mutation guard)
    skill = db.get(Skill, selected_skill_id)
    if skill is None or not skill.is_active:
        raise ConflictError(
            f"Skill {selected_skill_id} is no longer active in the catalog."
        )

    # Verify constraint eligibility at acceptance time (second gate)
    constraint_result = check_skill_constraints(skill, user.constraints)
    if not constraint_result.is_eligible:
        raise ConflictError(
            f"Skill no longer passes constraints: {'; '.join(constraint_result.reasons)}"
        )

    # Find or create the Quest for this skill
    quest = db.execute(
        select(Quest).where(
            and_(Quest.skill_id == skill.id, Quest.is_active == True)
        ).order_by(Quest.catalog_version.desc()).limit(1)
    ).scalar_one_or_none()
    if quest is None:
        # Auto-create a basic Quest for this skill if none exists
        quest = Quest(
            skill_id=skill.id,
            title=f"Quest: {skill.name}",
            description=skill.description,
            goal=f"Explore and experience: {skill.name}",
            catalog_version=skill.catalog_version,
        )
        db.add(quest)
        db.flush()

    # Create QuestAttempt
    attempt = QuestAttempt(
        user_id=user.id,
        quest_id=quest.id,
        skill_id=skill.id,
        skill_catalog_version=skill.catalog_version,
        activity_family_id=skill.activity_family_id,
        status=QuestAttemptStatus.PENDING.value,
    )
    db.add(attempt)
    db.flush()

    # Update recommendation
    rec.status = RecommendationStatus.ACCEPTED.value
    rec.selected_skill_id = selected_skill_id
    rec.responded_at = datetime.now(UTC)
    rec.resulting_quest_attempt_id = attempt.id

    db.commit()
    db.refresh(rec)
    db.refresh(attempt)

    log.info(
        "recommendation_accepted",
        recommendation_id=str(rec.id),
        skill_id=str(selected_skill_id),
        quest_attempt_id=str(attempt.id),
        user_id=str(user.id),
    )
    return rec, attempt


def reject_recommendation(
    db: Session,
    *,
    recommendation_id: uuid.UUID,
    reason: str | None,
    user: User,
) -> Recommendation:
    """Reject a recommendation (terminal state)."""
    rec = _get_recommendation_for_user(db, recommendation_id=recommendation_id, user=user)
    _assert_transition(rec, RecommendationStatus.REJECTED)
    rec.status = RecommendationStatus.REJECTED.value
    rec.responded_at = datetime.now(UTC)
    rec.rejection_reason = reason
    db.commit()
    db.refresh(rec)
    return rec


# ── Quest attempt transitions ─────────────────────────────────────────────────


def start_quest_attempt(
    db: Session, *, attempt_id: uuid.UUID, user: User
) -> QuestAttempt:
    """Transition a PENDING QuestAttempt to ACTIVE."""
    attempt = _get_attempt_for_user(db, attempt_id=attempt_id, user=user)
    _assert_quest_transition(attempt, QuestAttemptStatus.ACTIVE)
    attempt.status = QuestAttemptStatus.ACTIVE.value
    attempt.started_at = datetime.now(UTC)
    db.commit()
    db.refresh(attempt)
    return attempt


def complete_quest_attempt(
    db: Session, *, attempt_id: uuid.UUID, user: User
) -> QuestAttempt:
    """Transition an ACTIVE QuestAttempt to COMPLETED."""
    attempt = _get_attempt_for_user(db, attempt_id=attempt_id, user=user)
    _assert_quest_transition(attempt, QuestAttemptStatus.COMPLETED)
    attempt.status = QuestAttemptStatus.COMPLETED.value
    attempt.completed_at = datetime.now(UTC)
    db.commit()
    db.refresh(attempt)
    return attempt


def abandon_quest_attempt(
    db: Session,
    *,
    attempt_id: uuid.UUID,
    reason: str | None,
    user: User,
) -> QuestAttempt:
    """Transition an ACTIVE QuestAttempt to ABANDONED."""
    attempt = _get_attempt_for_user(db, attempt_id=attempt_id, user=user)
    _assert_quest_transition(attempt, QuestAttemptStatus.ABANDONED)
    attempt.status = QuestAttemptStatus.ABANDONED.value
    attempt.abandoned_at = datetime.now(UTC)
    attempt.abandonment_reason = reason
    db.commit()
    db.refresh(attempt)
    return attempt


# ── Internal helpers ──────────────────────────────────────────────────────────


def _get_recommendation_for_user(
    db: Session,
    *,
    recommendation_id: uuid.UUID,
    user: User,
) -> Recommendation:
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        raise NotFoundError(f"Recommendation {recommendation_id} not found.")
    if rec.user_id != user.id:
        raise ForbiddenError("You do not have access to this recommendation.")
    return rec


def _get_attempt_for_user(
    db: Session,
    *,
    attempt_id: uuid.UUID,
    user: User,
) -> QuestAttempt:
    attempt = db.get(QuestAttempt, attempt_id)
    if attempt is None:
        raise NotFoundError(f"QuestAttempt {attempt_id} not found.")
    if attempt.user_id != user.id:
        raise ForbiddenError("You do not have access to this quest attempt.")
    return attempt


def _assert_transition(rec: Recommendation, next_: RecommendationStatus) -> None:
    if not rec.can_transition_to(next_):
        raise InvalidTransitionError(
            f"Cannot transition recommendation from {rec.status!r} to {next_.value!r}."
        )


def _assert_quest_transition(attempt: QuestAttempt, next_: QuestAttemptStatus) -> None:
    if not attempt.can_transition_to(next_):
        raise InvalidTransitionError(
            f"Cannot transition quest attempt from {attempt.status!r} to {next_.value!r}."
        )
