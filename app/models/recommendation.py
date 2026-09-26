"""
Recommendation and RecommendationCandidate ORM models.

Lifecycle
---------
    PENDING ──► PRESENTED ──► ACCEPTED ──► (QuestAttempt created)
                    │
                    └──────► REJECTED ──► (terminal)
                    │
                    └──────► EXPIRED  ──► (terminal)

Rules
-----
* A Recommendation is per-user.
* Once ACCEPTED, a QuestAttempt is created – that attempt is the ground truth.
* Once REJECTED or EXPIRED, the recommendation is terminal.
* Candidates that are inactive or constraint-violating at selection time
  must be excluded — checked at generation time, not stored as eligible.
* The selected candidate's skill_id is snapshotted on creation.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class RecommendationStatus(str, enum.Enum):
    """Allowed statuses for a Recommendation."""

    PENDING = "pending"
    PRESENTED = "presented"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


RECOMMENDATION_TRANSITIONS: dict[RecommendationStatus, frozenset[RecommendationStatus]] = {
    RecommendationStatus.PENDING: frozenset({RecommendationStatus.PRESENTED}),
    RecommendationStatus.PRESENTED: frozenset(
        {
            RecommendationStatus.ACCEPTED,
            RecommendationStatus.REJECTED,
            RecommendationStatus.EXPIRED,
        }
    ),
    RecommendationStatus.ACCEPTED: frozenset(),   # terminal (attempt takes over)
    RecommendationStatus.REJECTED: frozenset(),   # terminal
    RecommendationStatus.EXPIRED: frozenset(),    # terminal
}


def is_valid_recommendation_transition(
    current: RecommendationStatus,
    next_: RecommendationStatus,
) -> bool:
    return next_ in RECOMMENDATION_TRANSITIONS.get(current, frozenset())


class NoveltyCategory(str, enum.Enum):
    """
    Canonical novelty categories used to classify a candidate skill
    relative to a user's exploration history.

    These are immutable semantic labels — not arbitrary numeric scores.
    The novelty engine assigns exactly one category per (user, skill) pair.
    """

    EXACT_REPETITION = "exact_repetition"
    # The exact skill has been attempted before (completed or abandoned).

    NEAR_DUPLICATE = "near_duplicate"
    # A near_duplicate relationship exists between this skill and a
    # previously experienced skill.

    SAME_FAMILY = "same_family"
    # The skill shares an activity family with a previously experienced skill,
    # but is not a near duplicate.

    RELATED_TERRITORY = "related_territory"
    # The skill is in a different family but within a category already explored,
    # or has complementary/progression relationships with explored skills.

    NEW_TERRITORY = "new_territory"
    # The skill is in a family not yet experienced, but in a category
    # the user has visited.

    UNEXPLORED_TERRITORY = "unexplored_territory"
    # The skill is in a category the user has never explored at all.


class Recommendation(TimestampMixin, Base):
    """
    A recommendation batch for a specific user.

    One Recommendation object represents one round of candidate generation.
    The user sees it as a single suggested quest.  Internally it can carry
    multiple ranked candidates; the user's chosen skill is recorded on
    ``selected_skill_id`` when they accept.
    """

    __tablename__ = "recommendations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','presented','accepted','rejected','expired')",
            name="ck_recommendation_valid_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=RecommendationStatus.PENDING.value,
        index=True,
    )
    presented_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Set when ACCEPTED – which candidate skill the user ultimately chose
    selected_skill_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    # The resulting QuestAttempt, set after ACCEPTED
    resulting_quest_attempt_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("quest_attempts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Human-readable context for why this recommendation was generated
    generation_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Phase 2 / MIX ─────────────────────────────────────────────────────
    is_mix_recommendation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    # The mix candidate ID if this recommendation arose from MIX MODE
    mix_candidate_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("mix_candidates.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Relationships ─────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="recommendations")  # type: ignore[name-defined]
    candidates: Mapped[list[RecommendationCandidate]] = relationship(
        "RecommendationCandidate",
        back_populates="recommendation",
        order_by="RecommendationCandidate.rank",
        lazy="select",
    )
    selected_skill: Mapped[Skill | None] = relationship(  # type: ignore[name-defined]
        "Skill", foreign_keys=[selected_skill_id], lazy="select"
    )
    resulting_quest_attempt: Mapped[QuestAttempt | None] = relationship(  # type: ignore[name-defined]
        "QuestAttempt", foreign_keys=[resulting_quest_attempt_id], lazy="select"
    )

    @property
    def status_enum(self) -> RecommendationStatus:
        return RecommendationStatus(self.status)

    def can_transition_to(self, next_: RecommendationStatus) -> bool:
        return is_valid_recommendation_transition(self.status_enum, next_)

    def __repr__(self) -> str:
        return f"<Recommendation id={self.id} user={self.user_id} status={self.status!r}>"


class RecommendationCandidate(TimestampMixin, Base):
    """
    A single ranked candidate skill within a Recommendation batch.

    Invariant
    ---------
    * The referenced skill MUST be active at generation time (enforced in
      the service layer — inactive skills are excluded during candidate
      generation, not just at display time).
    * Skill constraint eligibility is verified at generation time.
    * ``novelty_category`` records the deterministic novelty classification
      at the moment of generation.
    """

    __tablename__ = "recommendation_candidates"
    __table_args__ = (
        UniqueConstraint(
            "recommendation_id", "skill_id",
            name="uq_reccandidate_recommendation_skill",
        ),
        CheckConstraint(
            "rank > 0",
            name="ck_reccandidate_positive_rank",
        ),
        CheckConstraint(
            "score >= 0.0 AND score <= 1.0",
            name="ck_reccandidate_score_range",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Snapshot of catalog version at candidate generation time
    skill_catalog_version: Mapped[int] = mapped_column(Integer, nullable=False)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    novelty_category: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    # Human-readable explanation of why this candidate was chosen
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    recommendation: Mapped[Recommendation] = relationship(
        "Recommendation", back_populates="candidates"
    )
    skill: Mapped[Skill] = relationship("Skill", lazy="select")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return (
            f"<RecommendationCandidate rec={self.recommendation_id}"
            f" skill={self.skill_id} rank={self.rank}>"
        )


# Late imports
from app.models.catalog import Skill  # noqa: E402, F401
from app.models.quest import QuestAttempt  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
