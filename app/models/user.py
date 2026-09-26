"""
User and UserConstraints ORM models.

UserConstraints stores hard eligibility constraints (physical/equipment/time)
that must be checked against skills before any recommendation is generated.
Constraints are never overridden by AI or affinity logic.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class User(TimestampMixin, Base):
    """Application user account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(320), nullable=False, unique=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Exploration mode ──────────────────────────────────────────────────
    # "explore" (default, 95% novelty) | "locked" (LOCK IN — deep dive)
    exploration_mode: Mapped[str] = mapped_column(
        String(20), nullable=False, default="explore"
    )
    # Whether MIX MODE is currently enabled.
    mix_mode_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Minimum enjoyment score (1-10) for a skill to qualify for MIX suggestions.
    mix_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=8)

    # ── Relationships ─────────────────────────────────────────────────────
    constraints: Mapped[UserConstraints | None] = relationship(
        "UserConstraints", back_populates="user", uselist=False, lazy="select"
    )
    quest_attempts: Mapped[list[QuestAttempt]] = relationship(  # type: ignore[name-defined]
        "QuestAttempt", back_populates="user", lazy="dynamic"
    )
    recommendations: Mapped[list[Recommendation]] = relationship(  # type: ignore[name-defined]
        "Recommendation", back_populates="user", lazy="dynamic"
    )
    feedbacks: Mapped[list[Feedback]] = relationship(  # type: ignore[name-defined]
        "Feedback", back_populates="user", lazy="dynamic"
    )
    ratings: Mapped[list[Rating]] = relationship(  # type: ignore[name-defined]
        "Rating", back_populates="user", lazy="dynamic"
    )

    @property
    def is_locked_in(self) -> bool:
        return self.exploration_mode == "locked"

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} mode={self.exploration_mode}>"


class UserConstraints(TimestampMixin, Base):
    """
    Hard eligibility constraints for a user.

    These are non-negotiable filters applied before any skill is
    considered for recommendation.  They are never bypassed by
    affinity, DNA, or AI scoring.

    Physical constraints  – injuries, disabilities, pregnancy, etc.
    Equipment constraints – what the user does / doesn't own.
    Time constraints      – maximum session duration in minutes.
    """

    __tablename__ = "user_constraints"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,     # one constraints row per user
        index=True,
    )

    # ── Physical ──────────────────────────────────────────────────────────
    # Comma-separated constraint tags, e.g. "no_high_impact,no_overhead_reach"
    physical_restrictions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Equipment ─────────────────────────────────────────────────────────
    # Comma-separated tags of equipment the user DOES NOT have access to.
    equipment_exclusions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Time ──────────────────────────────────────────────────────────────
    # Maximum quest session length the user is willing to accept (minutes).
    max_session_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="constraints")

    def physical_restriction_set(self) -> frozenset[str]:
        """Return physical restrictions as a frozenset of tags."""
        if not self.physical_restrictions:
            return frozenset()
        return frozenset(t.strip() for t in self.physical_restrictions.split(",") if t.strip())

    def equipment_exclusion_set(self) -> frozenset[str]:
        """Return equipment exclusions as a frozenset of tags."""
        if not self.equipment_exclusions:
            return frozenset()
        return frozenset(t.strip() for t in self.equipment_exclusions.split(",") if t.strip())

    def __repr__(self) -> str:
        return f"<UserConstraints user_id={self.user_id}>"


# Avoid circular-import issues with forward references – resolved by Python
# at class instantiation time when all models are loaded.
from app.models.feedback import Feedback
from app.models.quest import QuestAttempt
from app.models.recommendation import Recommendation
