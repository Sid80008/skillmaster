"""
Tests for Recommendation state machine transitions.
"""
from __future__ import annotations

import pytest

from app.models.recommendation import (
    RecommendationStatus,
    is_valid_recommendation_transition,
)
from tests.conftest import (
    make_candidate,
    make_category,
    make_family,
    make_recommendation,
    make_skill,
    make_user,
)


class TestRecommendationTransitionLogic:
    """Pure unit tests for is_valid_recommendation_transition."""

    def test_pending_to_presented_is_valid(self):
        assert is_valid_recommendation_transition(
            RecommendationStatus.PENDING, RecommendationStatus.PRESENTED
        )

    def test_presented_to_accepted_is_valid(self):
        assert is_valid_recommendation_transition(
            RecommendationStatus.PRESENTED, RecommendationStatus.ACCEPTED
        )

    def test_presented_to_rejected_is_valid(self):
        assert is_valid_recommendation_transition(
            RecommendationStatus.PRESENTED, RecommendationStatus.REJECTED
        )

    def test_presented_to_expired_is_valid(self):
        assert is_valid_recommendation_transition(
            RecommendationStatus.PRESENTED, RecommendationStatus.EXPIRED
        )

    def test_pending_to_accepted_is_invalid(self):
        """Must be PRESENTED before ACCEPTED."""
        assert not is_valid_recommendation_transition(
            RecommendationStatus.PENDING, RecommendationStatus.ACCEPTED
        )

    def test_pending_to_rejected_is_invalid(self):
        assert not is_valid_recommendation_transition(
            RecommendationStatus.PENDING, RecommendationStatus.REJECTED
        )

    def test_accepted_is_terminal(self):
        for next_status in RecommendationStatus:
            assert not is_valid_recommendation_transition(
                RecommendationStatus.ACCEPTED, next_status
            )

    def test_rejected_is_terminal(self):
        for next_status in RecommendationStatus:
            assert not is_valid_recommendation_transition(
                RecommendationStatus.REJECTED, next_status
            )

    def test_expired_is_terminal(self):
        for next_status in RecommendationStatus:
            assert not is_valid_recommendation_transition(
                RecommendationStatus.EXPIRED, next_status
            )


class TestRecommendationServiceTransitions:
    """Integration tests via service layer."""

    def test_present_pending_recommendation(self, db):
        user = make_user(db)
        rec = make_recommendation(db, user=user, status="pending")

        from app.services.recommendation_service import present_recommendation
        updated = present_recommendation(db, recommendation_id=rec.id, user=user)
        assert updated.status == "presented"
        assert updated.presented_at is not None

    def test_present_already_presented_raises(self, db):
        user = make_user(db)
        rec = make_recommendation(db, user=user, status="presented")

        from app.services.exceptions import InvalidTransitionError
        from app.services.recommendation_service import present_recommendation
        with pytest.raises(InvalidTransitionError):
            present_recommendation(db, recommendation_id=rec.id, user=user)

    def test_reject_presented_recommendation(self, db):
        user = make_user(db)
        rec = make_recommendation(db, user=user, status="presented")

        from app.services.recommendation_service import reject_recommendation
        updated = reject_recommendation(
            db, recommendation_id=rec.id, reason="Not interested", user=user
        )
        assert updated.status == "rejected"
        assert updated.rejection_reason == "Not interested"

    def test_reject_accepted_recommendation_raises(self, db):
        user = make_user(db)
        rec = make_recommendation(db, user=user, status="accepted")

        from app.services.exceptions import InvalidTransitionError
        from app.services.recommendation_service import reject_recommendation
        with pytest.raises(InvalidTransitionError):
            reject_recommendation(db, recommendation_id=rec.id, reason=None, user=user)

    def test_accept_creates_quest_attempt(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        rec = make_recommendation(db, user=user, status="presented")
        make_candidate(db, recommendation=rec, skill=skill)

        from app.services.recommendation_service import accept_recommendation
        updated_rec, attempt = accept_recommendation(
            db,
            recommendation_id=rec.id,
            selected_skill_id=skill.id,
            user=user,
        )
        assert updated_rec.status == "accepted"
        assert updated_rec.selected_skill_id == skill.id
        assert attempt.skill_id == skill.id
        assert attempt.status == "pending"
        assert attempt.user_id == user.id

    def test_accept_with_wrong_skill_raises(self, db):
        """Selecting a skill not in the candidate list is rejected."""
        import uuid
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        rec = make_recommendation(db, user=user, status="presented")
        make_candidate(db, recommendation=rec, skill=skill)

        from app.services.exceptions import NotFoundError
        from app.services.recommendation_service import accept_recommendation
        with pytest.raises(NotFoundError):
            accept_recommendation(
                db,
                recommendation_id=rec.id,
                selected_skill_id=uuid.uuid4(),  # random ID not in candidates
                user=user,
            )
