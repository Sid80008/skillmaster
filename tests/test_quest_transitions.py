"""
Tests for QuestAttempt state machine transitions.

Covers:
- All valid transitions
- All invalid transitions (attempting an illegal next state)
"""
from __future__ import annotations

import pytest

from app.models.quest import (
    QuestAttemptStatus,
    is_valid_quest_attempt_transition,
    QUEST_ATTEMPT_TRANSITIONS,
)
from tests.conftest import make_user, make_category, make_family, make_skill, make_quest, make_attempt


class TestQuestAttemptTransitionLogic:
    """Unit tests for the pure transition-guard function."""

    def test_pending_to_active_is_valid(self):
        assert is_valid_quest_attempt_transition(
            QuestAttemptStatus.PENDING, QuestAttemptStatus.ACTIVE
        )

    def test_pending_to_cancelled_is_valid(self):
        assert is_valid_quest_attempt_transition(
            QuestAttemptStatus.PENDING, QuestAttemptStatus.CANCELLED
        )

    def test_active_to_completed_is_valid(self):
        assert is_valid_quest_attempt_transition(
            QuestAttemptStatus.ACTIVE, QuestAttemptStatus.COMPLETED
        )

    def test_active_to_abandoned_is_valid(self):
        assert is_valid_quest_attempt_transition(
            QuestAttemptStatus.ACTIVE, QuestAttemptStatus.ABANDONED
        )

    # ── Invalid transitions ───────────────────────────────────────────────

    def test_pending_to_completed_is_invalid(self):
        assert not is_valid_quest_attempt_transition(
            QuestAttemptStatus.PENDING, QuestAttemptStatus.COMPLETED
        )

    def test_pending_to_abandoned_is_invalid(self):
        assert not is_valid_quest_attempt_transition(
            QuestAttemptStatus.PENDING, QuestAttemptStatus.ABANDONED
        )

    def test_active_to_pending_is_invalid(self):
        assert not is_valid_quest_attempt_transition(
            QuestAttemptStatus.ACTIVE, QuestAttemptStatus.PENDING
        )

    def test_active_to_cancelled_is_invalid(self):
        assert not is_valid_quest_attempt_transition(
            QuestAttemptStatus.ACTIVE, QuestAttemptStatus.CANCELLED
        )

    def test_completed_is_terminal(self):
        """From COMPLETED, no transition is valid."""
        for next_status in QuestAttemptStatus:
            assert not is_valid_quest_attempt_transition(
                QuestAttemptStatus.COMPLETED, next_status
            )

    def test_abandoned_is_terminal(self):
        for next_status in QuestAttemptStatus:
            assert not is_valid_quest_attempt_transition(
                QuestAttemptStatus.ABANDONED, next_status
            )

    def test_cancelled_is_terminal(self):
        for next_status in QuestAttemptStatus:
            assert not is_valid_quest_attempt_transition(
                QuestAttemptStatus.CANCELLED, next_status
            )


class TestQuestAttemptServiceTransitions:
    """Integration tests via the recommendation_service state machine."""

    def test_start_pending_attempt(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="pending")

        from app.services.recommendation_service import start_quest_attempt
        updated = start_quest_attempt(db, attempt_id=attempt.id, user=user)
        assert updated.status == "active"
        assert updated.started_at is not None

    def test_start_already_active_attempt_raises(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="active")

        from app.services.recommendation_service import start_quest_attempt
        from app.services.exceptions import InvalidTransitionError
        with pytest.raises(InvalidTransitionError):
            start_quest_attempt(db, attempt_id=attempt.id, user=user)

    def test_complete_active_attempt(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="active")

        from app.services.recommendation_service import complete_quest_attempt
        updated = complete_quest_attempt(db, attempt_id=attempt.id, user=user)
        assert updated.status == "completed"
        assert updated.completed_at is not None

    def test_complete_pending_attempt_raises(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="pending")

        from app.services.recommendation_service import complete_quest_attempt
        from app.services.exceptions import InvalidTransitionError
        with pytest.raises(InvalidTransitionError):
            complete_quest_attempt(db, attempt_id=attempt.id, user=user)

    def test_abandon_active_attempt(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="active")

        from app.services.recommendation_service import abandon_quest_attempt
        updated = abandon_quest_attempt(
            db, attempt_id=attempt.id, reason="Too hard right now", user=user
        )
        assert updated.status == "abandoned"
        assert updated.abandoned_at is not None
        assert updated.abandonment_reason == "Too hard right now"

    def test_abandon_completed_attempt_raises(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        from app.services.recommendation_service import abandon_quest_attempt
        from app.services.exceptions import InvalidTransitionError
        with pytest.raises(InvalidTransitionError):
            abandon_quest_attempt(db, attempt_id=attempt.id, reason=None, user=user)

    def test_re_complete_completed_attempt_raises(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        from app.services.recommendation_service import complete_quest_attempt
        from app.services.exceptions import InvalidTransitionError
        with pytest.raises(InvalidTransitionError):
            complete_quest_attempt(db, attempt_id=attempt.id, user=user)
