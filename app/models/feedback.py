"""
Feedback ORM model.

A Feedback record captures the user's subjective response to a completed
or abandoned QuestAttempt.

Ownership invariant
-------------------
* A Feedback belongs to exactly one QuestAttempt.
* The QuestAttempt must belong to the same user as the Feedback.
* This is enforced at the service layer (cross-user writes return 403).
* Only COMPLETED or ABANDONED quest attempts can receive feedback.
* Each attempt can have at most one Feedback (enforced by UNIQUE constraint).

Immutability
------------
Feedback, once submitted, is an immutable historical record.
Rating and enjoyment_score can be updated by the user but are considered
soft mutable; the core identity (user_id, quest_attempt_id) is immutable.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
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


class Feedback(TimestampMixin, Base):
    """User feedback on a completed or abandoned QuestAttempt."""

    __tablename__ = "feedbacks"
    __table_args__ = (
        UniqueConstraint(
            "quest_attempt_id", name="uq_feedback_quest_attempt"
        ),
        CheckConstraint(
            "rating BETWEEN 1 AND 5",
            name="ck_feedback_rating_range",
        ),
        CheckConstraint(
            "enjoyment_score >= 0.0 AND enjoyment_score <= 1.0",
            name="ck_feedback_enjoyment_range",
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
    quest_attempt_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quest_attempts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # 1–5 star rating
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    # 0.0–1.0 normalised enjoyment (can differ from rating)
    enjoyment_score: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    # Free text reflection
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Structured tags the user applies (e.g. "too_easy,too_long")
    tags: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Would the user want to do this again?
    would_repeat: Mapped[bool | None] = mapped_column(nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="feedbacks")  # type: ignore[name-defined]
    quest_attempt: Mapped[QuestAttempt] = relationship(  # type: ignore[name-defined]
        "QuestAttempt", back_populates="feedback"
    )

    def tag_set(self) -> frozenset[str]:
        if not self.tags:
            return frozenset()
        return frozenset(t.strip() for t in self.tags.split(",") if t.strip())

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} attempt={self.quest_attempt_id} rating={self.rating}>"


# Late imports
from app.models.quest import QuestAttempt
from app.models.user import User
