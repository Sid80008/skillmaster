"""
Tests for exploration history correctness.

Verifies that:
- The history is derived purely from QuestAttempts
- Correct skill/family/category membership
- Meaningful experience requires being started, not just pending
- Completed and abandoned both count as meaningful
- Cancelled does NOT count
"""
from __future__ import annotations

import pytest

from app.models.quest import QuestAttemptStatus
from app.services.history_service import (
    get_exploration_summary,
    has_attempted_skill,
    has_completed_skill,
    has_meaningfully_experienced_skill,
    get_recent_attempts,
    get_recent_experienced_family_ids,
)
from tests.conftest import (
    make_user,
    make_category,
    make_family,
    make_skill,
    make_quest,
    make_attempt,
)


class TestExplorationHistory:

    def test_fresh_user_has_empty_history(self, db):
        user = make_user(db)
        summary = get_exploration_summary(db, user_id=user.id)
        assert len(summary.attempted_skill_ids) == 0
        assert len(summary.completed_skill_ids) == 0
        assert len(summary.meaningfully_experienced_skill_ids) == 0
        assert len(summary.experienced_family_ids) == 0

    def test_pending_attempt_counts_as_attempted(self, db):
        user = make_user(db)
        cat = make_category(db)
        fam = make_family(db, category=cat)
        skill = make_skill(db, family=fam)
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="pending")

        assert has_attempted_skill(db, user_id=user.id, skill_id=skill.id)
        assert not has_completed_skill(db, user_id=user.id, skill_id=skill.id)
        assert not has_meaningfully_experienced_skill(db, user_id=user.id, skill_id=skill.id)

    def test_pending_attempt_does_not_count_as_meaningful_experience(self, db):
        user = make_user(db)
        cat = make_category(db, slug="cat-pend")
        fam = make_family(db, category=cat, slug="fam-pend")
        skill = make_skill(db, family=fam, slug="skill-pend")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="pending")

        summary = get_exploration_summary(db, user_id=user.id)
        assert skill.id not in summary.meaningfully_experienced_skill_ids
        assert fam.id not in summary.experienced_family_ids

    def test_completed_attempt_is_fully_counted(self, db):
        user = make_user(db)
        cat = make_category(db, slug="cat-comp")
        fam = make_family(db, category=cat, slug="fam-comp")
        skill = make_skill(db, family=fam, slug="skill-comp")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        summary = get_exploration_summary(db, user_id=user.id)
        assert skill.id in summary.attempted_skill_ids
        assert skill.id in summary.completed_skill_ids
        assert skill.id in summary.meaningfully_experienced_skill_ids
        assert fam.id in summary.experienced_family_ids
        assert cat.id in summary.experienced_category_ids

    def test_abandoned_attempt_counts_as_meaningful(self, db):
        user = make_user(db)
        cat = make_category(db, slug="cat-aban")
        fam = make_family(db, category=cat, slug="fam-aban")
        skill = make_skill(db, family=fam, slug="skill-aban")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="abandoned")

        summary = get_exploration_summary(db, user_id=user.id)
        assert skill.id in summary.meaningfully_experienced_skill_ids
        assert fam.id in summary.experienced_family_ids
        assert not has_completed_skill(db, user_id=user.id, skill_id=skill.id)

    def test_cancelled_attempt_is_excluded_from_history(self, db):
        user = make_user(db)
        cat = make_category(db, slug="cat-canc")
        fam = make_family(db, category=cat, slug="fam-canc")
        skill = make_skill(db, family=fam, slug="skill-canc")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="cancelled")

        assert not has_attempted_skill(db, user_id=user.id, skill_id=skill.id)
        summary = get_exploration_summary(db, user_id=user.id)
        assert skill.id not in summary.attempted_skill_ids

    def test_multiple_users_histories_are_isolated(self, db):
        user_a = make_user(db, email="a@example.com", username="usera")
        user_b = make_user(db, email="b@example.com", username="userb")
        cat = make_category(db, slug="cat-iso")
        fam = make_family(db, category=cat, slug="fam-iso")
        skill = make_skill(db, family=fam, slug="skill-iso")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user_a, skill=skill, quest=quest, status="completed")

        # user_b should not see user_a's history
        assert not has_attempted_skill(db, user_id=user_b.id, skill_id=skill.id)
        summary_b = get_exploration_summary(db, user_id=user_b.id)
        assert skill.id not in summary_b.attempted_skill_ids

    def test_recent_family_ids_are_ordered_newest_first(self, db):
        from datetime import UTC, datetime, timedelta

        user = make_user(db)
        cat = make_category(db)
        fam1 = make_family(db, category=cat)
        fam2 = make_family(db, category=cat)
        skill1 = make_skill(db, family=fam1)
        skill2 = make_skill(db, family=fam2)
        quest1 = make_quest(db, skill=skill1)
        quest2 = make_quest(db, skill=skill2)

        now = datetime.now(UTC)
        attempt1 = make_attempt(db, user=user, skill=skill1, quest=quest1, status="completed")
        attempt2 = make_attempt(db, user=user, skill=skill2, quest=quest2, status="completed")

        # Force distinct created_at so ordering is deterministic
        attempt1.created_at = now - timedelta(seconds=10)
        attempt2.created_at = now
        db.flush()

        recent_families = get_recent_experienced_family_ids(db, user_id=user.id, window=10)
        # Most recent first (fam2 was done 10 seconds later)
        assert recent_families[0] == fam2.id
        assert recent_families[1] == fam1.id
