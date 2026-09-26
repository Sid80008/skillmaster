"""
Custom exception types used by service-layer code.

All exceptions here are caught by the FastAPI exception handlers
in ``app/main.py`` and translated into appropriate HTTP responses.
"""
from __future__ import annotations


class SkillQuestError(Exception):
    """Base class for all Skill Quest domain errors."""


class NotFoundError(SkillQuestError):
    """Raised when a requested resource does not exist (or is invisible to the user)."""


class ForbiddenError(SkillQuestError):
    """Raised when the current user does not own the requested resource."""


class ConflictError(SkillQuestError):
    """Raised when a duplicate or concurrent mutation is detected."""


class InvalidTransitionError(SkillQuestError):
    """Raised when an illegal state-machine transition is attempted."""


class ConstraintViolationError(SkillQuestError):
    """Raised when a user constraint (physical/equipment/time) is violated."""


class ValidationError(SkillQuestError):
    """Raised when input data fails domain-level validation."""
