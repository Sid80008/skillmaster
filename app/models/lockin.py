"""
Lock In and Mix candidates.
"""
from __future__ import annotations

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
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class LockInSession(TimestampMixin, Base):
    """Deep dive session into a single skill."""
    __tablename__ = "lockin_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False
    )
    
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    progression_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    unlock_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("status IN ('active','completed','unlocked')", name="ck_lockin_status"),
        CheckConstraint("progression_level >= 0 AND progression_level <= 4", name="ck_lockin_progression"),
    )


class MixCandidate(TimestampMixin, Base):
    """Potential mix discovered between two strong interests."""
    __tablename__ = "mix_candidates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_a_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    skill_b_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    
    result_skill_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"), nullable=True)
    
    mix_label: Mapped[str] = mapped_column(String(200), nullable=False)
    mix_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    is_presented: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("skill_a_id <> skill_b_id", name="ck_mix_no_self"),
        UniqueConstraint("user_id", "skill_a_id", "skill_b_id", name="uq_mix_user_skills"),
    )
