"""
Tests for feedback ownership, eligibility, and duplicate protection.
"""
from __future__ import annotations

import pytest

from app.services.exceptions import ConflictError, ForbiddenError, ValidationError
from app.services.feedback_service import submit_feedback, get_feedback_for_attempt
from tests.conftest import (
    make_user,
    make_category,
    make_family,
    make_skill,
    make_quest,
    make_attempt,
)


class TestFeedback:

    def test_submit_feedback_on_completed_attempt(self, db):
        user = make_user(db, email="fb1@example.com", username="fb1")
        cat = make_category(db, slug="cat-fb1")
        fam = make_family(db, category=cat, slug="fam-fb1")
        skill = make_skill(db, family=fam, slug="skill-fb1")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        fb = submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=4)
        assert fb.rating == 4
        assert fb.user_id == user.id
        assert fb.quest_attempt_id == attempt.id

    def test_submit_feedback_on_abandoned_attempt(self, db):
        user = make_user(db, email="fb2@example.com", username="fb2")
        cat = make_category(db, slug="cat-fb2")
        fam = make_family(db, category=cat, slug="fam-fb2")
        skill = make_skill(db, family=fam, slug="skill-fb2")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="abandoned")

        fb = submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=2)
        assert fb.rating == 2

    def test_submit_feedback_on_active_attempt_raises(self, db):
        user = make_user(db, email="fb3@example.com", username="fb3")
        cat = make_category(db, slug="cat-fb3")
        fam = make_family(db, category=cat, slug="fam-fb3")
        skill = make_skill(db, family=fam, slug="skill-fb3")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="active")

        with pytest.raises(ValidationError, match="COMPLETED or ABANDONED"):
            submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=3)

    def test_submit_feedback_on_pending_attempt_raises(self, db):
        user = make_user(db, email="fb4@example.com", username="fb4")
        cat = make_category(db, slug="cat-fb4")
        fam = make_family(db, category=cat, slug="fam-fb4")
        skill = make_skill(db, family=fam, slug="skill-fb4")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="pending")

        with pytest.raises(ValidationError):
            submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=3)

    def test_duplicate_feedback_raises_conflict(self, db):
        user = make_user(db, email="fb5@example.com", username="fb5")
        cat = make_category(db, slug="cat-fb5")
        fam = make_family(db, category=cat, slug="fam-fb5")
        skill = make_skill(db, family=fam, slug="skill-fb5")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=5)
        with pytest.raises(ConflictError, match="already exists"):
            submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=3)

    def test_feedback_from_wrong_user_raises_forbidden(self, db):
        owner = make_user(db, email="fb6o@example.com", username="fb6owner")
        intruder = make_user(db, email="fb6i@example.com", username="fb6intruder")
        cat = make_category(db, slug="cat-fb6")
        fam = make_family(db, category=cat, slug="fam-fb6")
        skill = make_skill(db, family=fam, slug="skill-fb6")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=owner, skill=skill, quest=quest, status="completed")

        with pytest.raises(ForbiddenError):
            submit_feedback(db, user=intruder, quest_attempt_id=attempt.id, rating=3)

    def test_invalid_rating_raises(self, db):
        user = make_user(db, email="fb7@example.com", username="fb7")
        cat = make_category(db, slug="cat-fb7")
        fam = make_family(db, category=cat, slug="fam-fb7")
        skill = make_skill(db, family=fam, slug="skill-fb7")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        with pytest.raises((ValidationError, Exception)):
            submit_feedback(db, user=user, quest_attempt_id=attempt.id, rating=6)

    def test_get_feedback_for_attempt_returns_none_before_submission(self, db):
        user = make_user(db, email="fb8@example.com", username="fb8")
        cat = make_category(db, slug="cat-fb8")
        fam = make_family(db, category=cat, slug="fam-fb8")
        skill = make_skill(db, family=fam, slug="skill-fb8")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        fb = get_feedback_for_attempt(db, quest_attempt_id=attempt.id, user=user)
        assert fb is None
