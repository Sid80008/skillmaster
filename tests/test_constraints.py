"""
Tests for constraint filtering.

Verifies that:
- Active skills with no conflicts pass
- Physical restriction tags are correctly evaluated
- Equipment exclusion tags are correctly evaluated
- Session duration limits are respected
- Inactive skills are rejected regardless of constraint state
"""
from __future__ import annotations

import pytest

from app.models.user import UserConstraints
from app.services.constraint_service import check_skill_constraints, filter_eligible_skills
from tests.conftest import (
    make_user,
    make_category,
    make_family,
    make_skill,
)


class TestConstraintFiltering:

    def _make_constraints(
        self,
        *,
        physical: str | None = None,
        equipment: str | None = None,
        max_minutes: int | None = None,
    ):
        """Create a lightweight fake constraints object (not DB-persisted).

        We use a SimpleNamespace so the constraint_service helper methods work
        without needing to hit the database.
        """
        from types import SimpleNamespace

        c = SimpleNamespace()
        c.physical_restrictions = physical
        c.equipment_exclusions = equipment
        c.max_session_minutes = max_minutes

        def physical_restriction_set():
            if not c.physical_restrictions:
                return frozenset()
            return frozenset(t.strip() for t in c.physical_restrictions.split(",") if t.strip())

        def equipment_exclusion_set():
            if not c.equipment_exclusions:
                return frozenset()
            return frozenset(t.strip() for t in c.equipment_exclusions.split(",") if t.strip())

        c.physical_restriction_set = physical_restriction_set
        c.equipment_exclusion_set = equipment_exclusion_set
        return c

    def test_active_skill_passes_no_constraints(self, db):
        cat = make_category(db, slug="cat-c1")
        fam = make_family(db, category=cat, slug="fam-c1")
        skill = make_skill(db, family=fam, slug="skill-c1")
        result = check_skill_constraints(skill, None)
        assert result.is_eligible
        assert not result.reasons

    def test_inactive_skill_always_fails(self, db):
        cat = make_category(db, slug="cat-c2")
        fam = make_family(db, category=cat, slug="fam-c2")
        skill = make_skill(db, family=fam, slug="skill-c2", is_active=False)
        result = check_skill_constraints(skill, None)
        assert not result.is_eligible
        assert any("not currently active" in r for r in result.reasons)

    def test_physical_restriction_conflict(self, db):
        cat = make_category(db, slug="cat-c3")
        fam = make_family(db, category=cat, slug="fam-c3")
        skill = make_skill(
            db, family=fam, slug="skill-c3",
            physical_tags="no_high_impact"
        )
        constraints = self._make_constraints(physical="no_high_impact")
        result = check_skill_constraints(skill, constraints)
        assert not result.is_eligible
        assert any("no_high_impact" in r for r in result.reasons)

    def test_no_physical_conflict_when_different_tags(self, db):
        cat = make_category(db, slug="cat-c4")
        fam = make_family(db, category=cat, slug="fam-c4")
        skill = make_skill(
            db, family=fam, slug="skill-c4",
            physical_tags="no_overhead_reach"
        )
        constraints = self._make_constraints(physical="no_high_impact")
        result = check_skill_constraints(skill, constraints)
        assert result.is_eligible

    def test_equipment_exclusion_conflict(self, db):
        cat = make_category(db, slug="cat-c5")
        fam = make_family(db, category=cat, slug="fam-c5")
        skill = make_skill(
            db, family=fam, slug="skill-c5",
            equipment_tags="climbing_harness"
        )
        constraints = self._make_constraints(equipment="climbing_harness")
        result = check_skill_constraints(skill, constraints)
        assert not result.is_eligible
        assert any("climbing_harness" in r for r in result.reasons)

    def test_no_equipment_conflict_when_user_has_it(self, db):
        cat = make_category(db, slug="cat-c6")
        fam = make_family(db, category=cat, slug="fam-c6")
        skill = make_skill(
            db, family=fam, slug="skill-c6",
            equipment_tags="bicycle"
        )
        constraints = self._make_constraints(equipment="climbing_harness")
        result = check_skill_constraints(skill, constraints)
        assert result.is_eligible

    def test_duration_exceeds_maximum(self, db):
        cat = make_category(db, slug="cat-c7")
        fam = make_family(db, category=cat, slug="fam-c7")
        skill = make_skill(db, family=fam, slug="skill-c7", duration=120)
        constraints = self._make_constraints(max_minutes=60)
        result = check_skill_constraints(skill, constraints)
        assert not result.is_eligible
        assert any("120 min" in r for r in result.reasons)

    def test_duration_within_maximum(self, db):
        cat = make_category(db, slug="cat-c8")
        fam = make_family(db, category=cat, slug="fam-c8")
        skill = make_skill(db, family=fam, slug="skill-c8", duration=45)
        constraints = self._make_constraints(max_minutes=60)
        result = check_skill_constraints(skill, constraints)
        assert result.is_eligible

    def test_filter_eligible_skills_returns_only_passing(self, db):
        cat = make_category(db, slug="cat-c9")
        fam = make_family(db, category=cat, slug="fam-c9")
        good_skill = make_skill(db, family=fam, slug="skill-c9-good")
        bad_skill = make_skill(
            db, family=fam, slug="skill-c9-bad",
            equipment_tags="bicycle"
        )
        constraints = self._make_constraints(equipment="bicycle")
        eligible = filter_eligible_skills([good_skill, bad_skill], constraints)
        assert good_skill in eligible
        assert bad_skill not in eligible

    def test_multiple_constraint_violations_all_reported(self, db):
        cat = make_category(db, slug="cat-c10")
        fam = make_family(db, category=cat, slug="fam-c10")
        skill = make_skill(
            db, family=fam, slug="skill-c10",
            physical_tags="no_high_impact",
            equipment_tags="bicycle",
            duration=120,
        )
        constraints = self._make_constraints(
            physical="no_high_impact",
            equipment="bicycle",
            max_minutes=60,
        )
        result = check_skill_constraints(skill, constraints)
        assert not result.is_eligible
        assert len(result.reasons) == 3
