"""
Constraint filtering service.

Checks whether a skill is eligible for a user given their hard constraints.

Rules (all are AND-conditions — one failure disqualifies the skill):
1. Skill must be is_active=True.
2. Skill must not require any equipment the user has excluded.
3. Skill must not have physical restriction tags overlapping the user's restrictions.
4. Skill's estimated_duration_minutes must not exceed user's max_session_minutes.

These checks are NOT overridable by AI, affinity, or any other system.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.catalog import Skill
from app.models.user import UserConstraints


@dataclass(frozen=True)
class ConstraintCheckResult:
    """Result of checking a skill against user constraints."""

    is_eligible: bool
    reasons: list[str]
    """Non-empty when is_eligible is False — explains each disqualification."""


def check_skill_constraints(
    skill: Skill,
    constraints: UserConstraints | None,
) -> ConstraintCheckResult:
    """
    Return whether *skill* passes all hard constraints for the user.

    Parameters
    ----------
    skill:
        The skill to evaluate.
    constraints:
        The user's UserConstraints row.  Pass ``None`` if the user has none —
        the skill still must be active.
    """
    reasons: list[str] = []

    # Rule 1: skill must be active in the catalog
    if not skill.is_active:
        reasons.append("Skill is not currently active in the catalog.")
        return ConstraintCheckResult(is_eligible=False, reasons=reasons)

    if constraints is None:
        return ConstraintCheckResult(is_eligible=True, reasons=[])

    # Rule 2: physical restrictions
    user_restrictions = constraints.physical_restriction_set()
    skill_restrictions = skill.physical_restriction_tag_set()
    conflicting_physical = user_restrictions & skill_restrictions
    if conflicting_physical:
        reasons.append(
            f"Skill requires physical capability that conflicts with user restriction: "
            f"{', '.join(sorted(conflicting_physical))}"
        )

    # Rule 3: equipment exclusions
    user_equipment_excluded = constraints.equipment_exclusion_set()
    skill_required_equipment = skill.required_equipment_tag_set()
    missing_equipment = user_equipment_excluded & skill_required_equipment
    if missing_equipment:
        reasons.append(
            f"Skill requires equipment the user does not have: "
            f"{', '.join(sorted(missing_equipment))}"
        )

    # Rule 4: session duration
    if (
        constraints.max_session_minutes is not None
        and skill.estimated_duration_minutes > constraints.max_session_minutes
    ):
        reasons.append(
            f"Skill requires {skill.estimated_duration_minutes} min; "
            f"user maximum is {constraints.max_session_minutes} min."
        )

    return ConstraintCheckResult(is_eligible=len(reasons) == 0, reasons=reasons)


def filter_eligible_skills(
    skills: list[Skill],
    constraints: UserConstraints | None,
) -> list[Skill]:
    """Return only the skills from *skills* that pass all constraints."""
    return [
        skill
        for skill in skills
        if check_skill_constraints(skill, constraints).is_eligible
    ]
