"""
Challenge ORM model.

A Challenge represents a concrete weekend quest tied to a Skill.
"""
from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class Challenge(TimestampMixin, Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(String(300), nullable=True)
    
    # ── Challenge Structure ────────────────────────────────────────────────
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    learn_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    do_content: Mapped[str] = mapped_column(Text, nullable=False)
    finish_criteria: Mapped[str] = mapped_column(Text, nullable=False)
    stretch_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    why_this_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    resources: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # ── Metadata ───────────────────────────────────────────────────────────
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    __table_args__ = (
        CheckConstraint("difficulty_level BETWEEN 1 AND 5", name="ck_challenge_difficulty"),
    )
