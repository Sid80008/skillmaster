"""
Tests for user ownership isolation.

Business invariant: a user must never be able to read, write, or transition
resources owned by a different user.
"""
from __future__ import annotations

import uuid

import pytest

from app.services.exceptions import ForbiddenError, NotFoundError
from tests.conftest import (
    make_user,
    make_category,
    make_family,
    make_skill,
    make_quest,
    make_attempt,
    make_recommendation,
    make_candidate,
)


class TestUserOwnershipIsolation:

    def test_start_other_users_attempt_raises_forbidden(self, db):
        owner = make_user(db, email="owner@example.com", username="owner")
        intruder = make_user(db, email="intruder@example.com", username="intruder")
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=owner, skill=skill, quest=quest, status="pending")

        from app.services.recommendation_service import start_quest_attempt
        with pytest.raises(ForbiddenError):
            start_quest_attempt(db, attempt_id=attempt.id, user=intruder)

    def test_complete_other_users_attempt_raises_forbidden(self, db):
        owner = make_user(db, email="owner2@example.com", username="owner2")
        intruder = make_user(db, email="intruder2@example.com", username="intruder2")
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam, slug="skill-x")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=owner, skill=skill, quest=quest, status="active")

        from app.services.recommendation_service import complete_quest_attempt
        with pytest.raises(ForbiddenError):
            complete_quest_attempt(db, attempt_id=attempt.id, user=intruder)

    def test_present_other_users_recommendation_raises_forbidden(self, db):
        owner = make_user(db, email="owner3@example.com", username="owner3")
        intruder = make_user(db, email="intruder3@example.com", username="intruder3")
        rec = make_recommendation(db, user=owner, status="pending")

        from app.services.recommendation_service import present_recommendation
        with pytest.raises(ForbiddenError):
            present_recommendation(db, recommendation_id=rec.id, user=intruder)

    def test_reject_other_users_recommendation_raises_forbidden(self, db):
        owner = make_user(db, email="owner4@example.com", username="owner4")
        intruder = make_user(db, email="intruder4@example.com", username="intruder4")
        rec = make_recommendation(db, user=owner, status="presented")

        from app.services.recommendation_service import reject_recommendation
        with pytest.raises(ForbiddenError):
            reject_recommendation(db, recommendation_id=rec.id, reason=None, user=intruder)

    def test_feedback_on_other_users_attempt_raises_forbidden(self, db):
        owner = make_user(db, email="owner5@example.com", username="owner5")
        intruder = make_user(db, email="intruder5@example.com", username="intruder5")
        cat = make_category(db, slug="cat2")
        fam = make_family(db, category=cat, slug="fam2")
        skill = make_skill(db, family=fam, slug="skill2")
        quest = make_quest(db, skill=skill)
        attempt = make_attempt(db, user=owner, skill=skill, quest=quest, status="completed")

        from app.services.feedback_service import submit_feedback
        with pytest.raises(ForbiddenError):
            submit_feedback(
                db,
                user=intruder,
                quest_attempt_id=attempt.id,
                rating=4,
            )

    def test_nonexistent_attempt_raises_not_found(self, db):
        user = make_user(db, email="ghost@example.com", username="ghost")

        from app.services.recommendation_service import start_quest_attempt
        with pytest.raises(NotFoundError):
            start_quest_attempt(db, attempt_id=uuid.uuid4(), user=user)

    def test_nonexistent_recommendation_raises_not_found(self, db):
        user = make_user(db, email="ghost2@example.com", username="ghost2")

        from app.services.recommendation_service import present_recommendation
        with pytest.raises(NotFoundError):
            present_recommendation(db, recommendation_id=uuid.uuid4(), user=user)
