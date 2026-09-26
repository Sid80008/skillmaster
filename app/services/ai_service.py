"""
AI service boundary.

This module defines the interface through which AI/ML components may
*optionally* enrich the recommendation pipeline.

Design contract
---------------
* AI is advisory only.
* If the AI service is unavailable or raises any error, the system falls
  back to deterministic logic without surfacing the failure to the user.
* AI may adjust candidate *scores* within novelty tiers but CANNOT:
    - promote an ineligible skill to eligible
    - change a NoveltyCategory classification
    - override constraint filtering
    - change which candidate was ultimately selected
* This module contains no external HTTP calls yet.  It provides the
  interface stub that future AI integrations should implement.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class AIAffinityScore:
    """AI-provided affinity adjustment for a single skill candidate."""

    skill_id: str
    affinity_delta: float   # bounded: -0.2 to +0.2 — cannot dominate novelty
    rationale: str | None


class AIAffinityProvider(Protocol):
    """
    Protocol (interface) for AI affinity providers.

    Future implementations (e.g., Gemini-based) should implement this
    protocol.  The recommendation service calls ``score_candidates`` and
    applies the deltas as an additive adjustment to novelty scores.
    """

    def score_candidates(
        self,
        user_id: str,
        candidate_skill_ids: list[str],
        context: dict,
    ) -> list[AIAffinityScore]:
        """
        Return affinity scores for the given candidate skills.

        Implementations MUST:
        - Return within a reasonable timeout.
        - Return only skill IDs that were passed in.
        - Clamp affinity_delta to [-0.2, +0.2].
        - Return an empty list (not raise) if scoring fails.
        """
        ...


class NullAffinityProvider:
    """
    Default no-op provider.

    Used when no AI service is configured or when AI is unavailable.
    Returns empty scores so the pipeline continues with pure deterministic
    ranking.
    """

    def score_candidates(
        self,
        user_id: str,
        candidate_skill_ids: list[str],
        context: dict,
    ) -> list[AIAffinityScore]:
        log.debug("ai_affinity_provider_null", user_id=user_id)
        return []


# Module-level singleton — swap in a real provider at startup if configured.
_affinity_provider: AIAffinityProvider = NullAffinityProvider()


def get_affinity_provider() -> AIAffinityProvider:
    """Return the current AI affinity provider."""
    return _affinity_provider


def set_affinity_provider(provider: AIAffinityProvider) -> None:
    """Replace the affinity provider (called at application startup)."""
    global _affinity_provider
    _affinity_provider = provider
    log.info("ai_affinity_provider_set", provider=type(provider).__name__)


def safe_score_candidates(
    user_id: str,
    candidate_skill_ids: list[str],
    context: dict,
) -> list[AIAffinityScore]:
    """
    Call the affinity provider, catching and logging all errors.

    Always returns a (possibly empty) list — the pipeline must not fail
    because AI is unavailable.
    """
    try:
        return _affinity_provider.score_candidates(user_id, candidate_skill_ids, context)
    except Exception as exc:
        log.warning("ai_affinity_error", error=str(exc), user_id=user_id)
        return []
