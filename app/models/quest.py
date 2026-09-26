"""
Quest and QuestAttempt ORM models.

State machine
-------------
QuestAttempt follows a strict, server-enforced state machine:

    PENDING ──► ACTIVE ──► COMPLETED
                  │
                  └──────► ABANDONED

Rules
-----
* Only ACTIVE attempts may transition to COMPLETED or ABANDONED.
* PENDING may only advance to ACTIVE (start) or be cancelled (→ CANCELLED).
* COMPLETED and ABANDONED are terminal — no further transitions.
* completed_at / abandoned_at are set only once (immutable afterwards).
* The snapshot of which skill version was attempted is stored on the attempt
  so that catalog mutations cannot retroactively change history.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class QuestAttemptStatus(str, enum.Enum):
    """Allowed statuses for a QuestAttempt."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"   # Recommendation rejected before attempt started


# Valid transitions: current_status → set of allowed next statuses
QUEST_ATTEMPT_TRANSITIONS: dict[QuestAttemptStatus, frozenset[QuestAttemptStatus]] = {
    QuestAttemptStatus.PENDING: frozenset(
        {QuestAttemptStatus.ACTIVE, QuestAttemptStatus.CANCELLED}
    ),
    QuestAttemptStatus.ACTIVE: frozenset(
        {QuestAttemptStatus.COMPLETED, QuestAttemptStatus.ABANDONED}
    ),
    QuestAttemptStatus.COMPLETED: frozenset(),   # terminal
    QuestAttemptStatus.ABANDONED: frozenset(),   # terminal
    QuestAttemptStatus.CANCELLED: frozenset(),   # terminal
}


def is_valid_quest_attempt_transition(
    current: QuestAttemptStatus,
    next_: QuestAttemptStatus,
) -> bool:
    """Return True if transitioning from *current* to *next_* is legal."""
    return next_ in QUEST_ATTEMPT_TRANSITIONS.get(current, frozenset())


class Quest(TimestampMixin, Base):
    """
    A Quest is a named challenge template that can be attempted.

    A Quest wraps a single Skill with a specific framing / goal context.
    It is the unit that gets recommended and attempted.
    """

    __tablename__ = "quests"
    __table_args__ = (
        UniqueConstraint("skill_id", "catalog_version", name="uq_quest_skill_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        nullable=False, default=True
    )
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ── Relationships ─────────────────────────────────────────────────────
    skill: Mapped[Skill] = relationship("Skill", lazy="select")  # type: ignore[name-defined]
    attempts: Mapped[list[QuestAttempt]] = relationship(
        "QuestAttempt", back_populates="quest", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Quest id={self.id} title={self.title!r}>"


class QuestAttempt(TimestampMixin, Base):
    """
    An immutable record of a user attempting a specific Quest.

    Immutability contract
    ---------------------
    * ``user_id``, ``quest_id``, ``skill_id``, ``skill_catalog_version``
      are set at creation and NEVER changed.
    * Status can only advance along the defined state machine.
    * ``completed_at`` and ``abandoned_at`` are written at most once.

    Exploration history
    -------------------
    QuestAttempts are the authoritative source of exploration history.
    Profile / DNA data is derived — never the source of truth for:
    - Has user attempted this skill?
    - Has user completed this skill?
    - Which activity families has the user experienced?
    """

    __tablename__ = "quest_attempts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','active','completed','abandoned','cancelled')",
            name="ck_questattempt_valid_status",
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
    quest_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("quests.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Snapshot: the skill UUID this attempt was for (immutable)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    # Snapshot: the catalog version at the time the attempt was created
    skill_catalog_version: Mapped[int] = mapped_column(Integer, nullable=False)
    # Snapshot: the activity family UUID at attempt creation time
    activity_family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_families.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # The concrete Challenge selected for this attempt
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("challenges.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[str] = mapped_column(

        String(20),
        nullable=False,
        default=QuestAttemptStatus.PENDING.value,
        index=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    abandoned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Optional user-supplied notes at abandonment
    abandonment_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="quest_attempts")  # type: ignore[name-defined]
    quest: Mapped[Quest] = relationship("Quest", back_populates="attempts")
    skill: Mapped[Skill] = relationship("Skill", lazy="select")  # type: ignore[name-defined]
    activity_family: Mapped[ActivityFamily] = relationship("ActivityFamily", lazy="select")  # type: ignore[name-defined]
    feedback: Mapped[Feedback | None] = relationship(  # type: ignore[name-defined]
        "Feedback", back_populates="quest_attempt", uselist=False
    )

    @property
    def status_enum(self) -> QuestAttemptStatus:
        return QuestAttemptStatus(self.status)

    def can_transition_to(self, next_: QuestAttemptStatus) -> bool:
        return is_valid_quest_attempt_transition(self.status_enum, next_)

    @property
    def skill_name(self) -> str | None:
        return self.skill.name if self.skill else None

    @property
    def activity_family_name(self) -> str | None:
        return self.activity_family.name if self.activity_family else None

    def __repr__(self) -> str:
        return f"<QuestAttempt id={self.id} user={self.user_id} status={self.status!r}>"


# Late imports to break circular refs
from app.models.catalog import ActivityFamily, Skill  # noqa: E402, F401
from app.models.feedback import Feedback  # noqa: E402, F401
from app.models.user import User  # noqa: E402, F401
