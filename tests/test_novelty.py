"""
Tests for deterministic novelty classification.

Verifies that the novelty engine correctly assigns NoveltyCategory values
based on history and catalog relationships — not AI or profile data.
"""
from __future__ import annotations

from app.models.catalog import SkillRelationship
from app.models.recommendation import NoveltyCategory
from app.services.history_service import ExplorationSummary, get_exploration_summary
from app.services.novelty_service import (
    INELIGIBLE_NOVELTY_CATEGORIES,
    classify_novelty,
    is_novelty_eligible,
    novelty_score,
)
from tests.conftest import (
    make_attempt,
    make_category,
    make_family,
    make_quest,
    make_skill,
    make_user,
)


class TestNoveltyClassification:

    def _empty_summary(self) -> ExplorationSummary:
        return ExplorationSummary(
            attempted_skill_ids=frozenset(),
            completed_skill_ids=frozenset(),
            meaningfully_experienced_skill_ids=frozenset(),
            experienced_family_ids=frozenset(),
            experienced_category_ids=frozenset(),
        )

    def test_exact_repetition_when_skill_experienced(self, db):
        user = make_user(db)
        cat = make_category(db, slug="cat-er")
        fam = make_family(db, category=cat, slug="fam-er")
        skill = make_skill(db, family=fam, slug="skill-er")
        quest = make_quest(db, skill=skill)
        make_attempt(db, user=user, skill=skill, quest=quest, status="completed")

        summary = get_exploration_summary(db, user_id=user.id)
        category = classify_novelty(skill, summary, db)
        assert category == NoveltyCategory.EXACT_REPETITION

    def test_near_duplicate_from_relationship(self, db):
        cat = make_category(db, slug="cat-nd")
        fam = make_family(db, category=cat, slug="fam-nd")
        skill_orig = make_skill(db, family=fam, slug="skill-orig")
        skill_dup = make_skill(db, family=fam, slug="skill-dup")

        # Create near_duplicate relationship
        rel = SkillRelationship(
            from_skill_id=skill_dup.id,
            to_skill_id=skill_orig.id,
            relationship_type="near_duplicate",
        )
        db.add(rel)
        db.flush()

        # User has experienced skill_orig
        summary = ExplorationSummary(
            attempted_skill_ids=frozenset({skill_orig.id}),
            completed_skill_ids=frozenset({skill_orig.id}),
            meaningfully_experienced_skill_ids=frozenset({skill_orig.id}),
            experienced_family_ids=frozenset({fam.id}),
            experienced_category_ids=frozenset({cat.id}),
        )

        category = classify_novelty(skill_dup, summary, db)
        assert category == NoveltyCategory.NEAR_DUPLICATE

    def test_same_family_classification(self, db):
        cat = make_category(db, slug="cat-sf")
        fam = make_family(db, category=cat, slug="fam-sf")
        skill_a = make_skill(db, family=fam, slug="skill-sf-a")
        skill_b = make_skill(db, family=fam, slug="skill-sf-b")

        # User has experienced skill_a (not skill_b)
        summary = ExplorationSummary(
            attempted_skill_ids=frozenset({skill_a.id}),
            completed_skill_ids=frozenset({skill_a.id}),
            meaningfully_experienced_skill_ids=frozenset({skill_a.id}),
            experienced_family_ids=frozenset({fam.id}),
            experienced_category_ids=frozenset({cat.id}),
        )

        category = classify_novelty(skill_b, summary, db)
        assert category == NoveltyCategory.SAME_FAMILY

    def test_related_territory_same_category_different_family(self, db):
        cat = make_category(db, slug="cat-rt")
        fam_experienced = make_family(db, category=cat, slug="fam-rt-exp")
        fam_new = make_family(db, category=cat, slug="fam-rt-new")
        skill_exp = make_skill(db, family=fam_experienced, slug="skill-rt-exp")
        skill_new = make_skill(db, family=fam_new, slug="skill-rt-new")

        summary = ExplorationSummary(
            attempted_skill_ids=frozenset({skill_exp.id}),
            completed_skill_ids=frozenset({skill_exp.id}),
            meaningfully_experienced_skill_ids=frozenset({skill_exp.id}),
            experienced_family_ids=frozenset({fam_experienced.id}),
            experienced_category_ids=frozenset({cat.id}),
        )

        category = classify_novelty(skill_new, summary, db)
        assert category == NoveltyCategory.RELATED_TERRITORY

    def test_new_territory_unexplored_category(self, db):
        cat_explored = make_category(db, slug="cat-nt-old")
        cat_new = make_category(db, slug="cat-nt-new")
        fam_old = make_family(db, category=cat_explored, slug="fam-nt-old")
        fam_new = make_family(db, category=cat_new, slug="fam-nt-new")
        skill_old = make_skill(db, family=fam_old, slug="skill-nt-old")
        skill_new = make_skill(db, family=fam_new, slug="skill-nt-new")

        summary = ExplorationSummary(
            attempted_skill_ids=frozenset({skill_old.id}),
            completed_skill_ids=frozenset({skill_old.id}),
            meaningfully_experienced_skill_ids=frozenset({skill_old.id}),
            experienced_family_ids=frozenset({fam_old.id}),
            experienced_category_ids=frozenset({cat_explored.id}),
        )

        category = classify_novelty(skill_new, summary, db)
        assert category == NoveltyCategory.NEW_TERRITORY

    def test_unexplored_territory_brand_new_user(self, db):
        cat = make_category(db, slug="cat-ut")
        fam = make_family(db, category=cat, slug="fam-ut")
        skill = make_skill(db, family=fam, slug="skill-ut")

        summary = self._empty_summary()
        category = classify_novelty(skill, summary, db)
        assert category == NoveltyCategory.UNEXPLORED_TERRITORY

    def test_exact_repetition_is_ineligible(self):
        assert NoveltyCategory.EXACT_REPETITION in INELIGIBLE_NOVELTY_CATEGORIES
        assert not is_novelty_eligible(NoveltyCategory.EXACT_REPETITION)

    def test_near_duplicate_is_ineligible(self):
        assert NoveltyCategory.NEAR_DUPLICATE in INELIGIBLE_NOVELTY_CATEGORIES
        assert not is_novelty_eligible(NoveltyCategory.NEAR_DUPLICATE)

    def test_same_family_is_eligible(self):
        assert is_novelty_eligible(NoveltyCategory.SAME_FAMILY)

    def test_unexplored_territory_has_highest_novelty_score(self):
        assert novelty_score(NoveltyCategory.UNEXPLORED_TERRITORY) == 1.0

    def test_exact_repetition_has_zero_novelty_score(self):
        assert novelty_score(NoveltyCategory.EXACT_REPETITION) == 0.0

    def test_novelty_score_ordering(self):
        """Scores must be in decreasing order of novelty."""
        scores = [
            novelty_score(NoveltyCategory.UNEXPLORED_TERRITORY),
            novelty_score(NoveltyCategory.NEW_TERRITORY),
            novelty_score(NoveltyCategory.RELATED_TERRITORY),
            novelty_score(NoveltyCategory.SAME_FAMILY),
            novelty_score(NoveltyCategory.NEAR_DUPLICATE),
            novelty_score(NoveltyCategory.EXACT_REPETITION),
        ]
        assert scores == sorted(scores, reverse=True)
