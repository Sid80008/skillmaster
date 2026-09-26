"""
Tests for recommendation candidate eligibility and the recommendation pipeline.

Verifies:
- Inactive skills are excluded from candidates
- Constraint-failing skills are excluded
- Novelty-ineligible skills (exact repetition, near duplicate) are excluded
- Duplicate recommendation guard (ConflictError when open rec exists)
- The recommendation pipeline produces valid, ranked candidates
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.recommendation import NoveltyCategory, RecommendationStatus
from app.services.exceptions import ConflictError
from app.services.recommendation_service import create_recommendation
from tests.conftest import (
    make_attempt,
    make_category,
    make_family,
    make_quest,
    make_skill,
    make_user,
)


class TestRecommendationCandidateEligibility:

    def test_inactive_skill_not_in_candidates(self, db):
        """An inactive skill must never appear as a candidate."""
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        inactive_skill = make_skill(db, family=fam, is_active=False)
        # Add an active skill so the pipeline can produce a recommendation
        active_skill = make_skill(db, family=fam)

        rec = create_recommendation(db, user=user)
        candidate_skill_ids = {c.skill_id for c in rec.candidates}
        assert inactive_skill.id not in candidate_skill_ids, (
            "Inactive skill must not appear in recommendation candidates."
        )

    def test_constraint_failing_skill_not_in_candidates(self, db):
        """A skill that fails constraints must never appear as a candidate."""
        from app.models.user import UserConstraints

        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        # Skill requires bicycle equipment
        blocked_skill = make_skill(db, family=fam, equipment_tags="bicycle_x123")
        # Add a non-blocked skill so the pipeline can run
        allowed_skill = make_skill(db, family=fam)

        # Give the user a constraint that blocks bicycle_x123
        constraints = UserConstraints(
            user_id=user.id,
            equipment_exclusions="bicycle_x123",
        )
        db.add(constraints)
        db.flush()
        db.refresh(user)

        rec = create_recommendation(db, user=user)
        candidate_skill_ids = {c.skill_id for c in rec.candidates}
        assert blocked_skill.id not in candidate_skill_ids, (
            "Constraint-failing skill must not appear in recommendation candidates."
        )

    def test_experienced_skill_not_recommended_again(self, db):
        """A skill in EXACT_REPETITION category must be excluded from candidates."""
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        experienced_skill = make_skill(db, family=fam)
        novel_skill = make_skill(db, family=fam)  # gives the pipeline something eligible

        quest = make_quest(db, skill=experienced_skill)
        # User has completed the experienced_skill
        make_attempt(db, user=user, skill=experienced_skill, quest=quest, status="completed")

        rec = create_recommendation(db, user=user)
        candidate_skill_ids = {c.skill_id for c in rec.candidates}
        assert experienced_skill.id not in candidate_skill_ids, (
            "Already-experienced (EXACT_REPETITION) skill must not appear in candidates."
        )

    def test_successful_recommendation_creation(self, db):
        """Happy-path: at least one eligible skill → recommendation created."""
        user = make_user(db, email="re4@example.com", username="re4")
        cat = make_category(db, slug="cat-re4")
        fam = make_family(db, category=cat, slug="fam-re4")
        make_skill(db, family=fam, slug="skill-re4-a")
        make_skill(db, family=fam, slug="skill-re4-b")

        rec = create_recommendation(db, user=user)
        assert rec.status == RecommendationStatus.PENDING.value
        assert rec.user_id == user.id
        assert len(rec.candidates) >= 1

    def test_candidates_are_ranked_from_one(self, db):
        user = make_user(db, email="re5@example.com", username="re5")
        cat = make_category(db, slug="cat-re5")
        fam = make_family(db, category=cat, slug="fam-re5")
        for i in range(3):
            make_skill(db, family=fam, slug=f"skill-re5-{i}")

        rec = create_recommendation(db, user=user)
        ranks = [c.rank for c in rec.candidates]
        assert min(ranks) == 1
        assert sorted(ranks) == list(range(1, len(ranks) + 1))

    def test_duplicate_recommendation_raises_conflict(self, db):
        """Cannot create a new recommendation if one is already open."""
        user = make_user(db, email="re6@example.com", username="re6")
        cat = make_category(db, slug="cat-re6")
        fam = make_family(db, category=cat, slug="fam-re6")
        make_skill(db, family=fam, slug="skill-re6")

        # First recommendation OK
        create_recommendation(db, user=user)

        # Second should raise ConflictError
        with pytest.raises(ConflictError, match="open recommendation"):
            create_recommendation(db, user=user)

    def test_candidate_novelty_category_is_valid_enum_value(self, db):
        user = make_user(db, email="re7@example.com", username="re7")
        cat = make_category(db, slug="cat-re7")
        fam = make_family(db, category=cat, slug="fam-re7")
        make_skill(db, family=fam, slug="skill-re7")

        rec = create_recommendation(db, user=user)
        valid_values = {c.value for c in NoveltyCategory}
        for candidate in rec.candidates:
            assert candidate.novelty_category in valid_values

    def test_candidate_score_is_within_bounds(self, db):
        user = make_user(db, email="re8@example.com", username="re8")
        cat = make_category(db, slug="cat-re8")
        fam = make_family(db, category=cat, slug="fam-re8")
        make_skill(db, family=fam, slug="skill-re8")

        rec = create_recommendation(db, user=user)
        for candidate in rec.candidates:
            assert Decimal(0) <= candidate.score <= Decimal(1)
