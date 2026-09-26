"""
Multi-dimensional Rating model.

Replaces the simple feedback model to capture nuance: interest, enjoyment, curiosity, etc.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class Rating(TimestampMixin, Base):
    __tablename__ = "ratings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    quest_attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quest_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("challenges.id", ondelete="SET NULL"), nullable=True
    )

    # ── Pre-experience signal ──
    pre_interest: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Post-experience signals ──
    enjoyment: Mapped[int] = mapped_column(Integer, nullable=False)
    curiosity: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_felt: Mapped[int | None] = mapped_column(Integer, nullable=True)
    would_repeat: Mapped[str] = mapped_column(String(10), nullable=False)
    deep_dive_interest: Mapped[int] = mapped_column(Integer, nullable=False)
    
    standout_moment: Mapped[str | None] = mapped_column(Text, nullable=True)
    friction_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    free_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Computed signals ──
    composite_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    affinity_signal: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)

    # ── Relationships ──
    user = relationship("User", back_populates="ratings")

    __table_args__ = (
        CheckConstraint("enjoyment BETWEEN 1 AND 10", name="ck_rating_enjoyment"),
        CheckConstraint("curiosity BETWEEN 1 AND 10", name="ck_rating_curiosity"),
        CheckConstraint("pre_interest BETWEEN 1 AND 10", name="ck_rating_pre_interest"),
        CheckConstraint("deep_dive_interest BETWEEN 1 AND 10", name="ck_rating_deep_dive"),
        CheckConstraint("difficulty_felt BETWEEN 1 AND 10", name="ck_rating_difficulty"),
        CheckConstraint("would_repeat IN ('yes','maybe','no')", name="ck_rating_repeat"),
        UniqueConstraint("quest_attempt_id", name="uq_rating_quest_attempt"),
    )
