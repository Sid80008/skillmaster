"""
Skill DNA and User Category Profiles.

Stores the underlying extracted traits and broad category affinities of the user.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.mixins import TimestampMixin, new_uuid


class SkillDNA(TimestampMixin, Base):
    """Underlying characteristic affinity derived from all experiences."""
    __tablename__ = "skill_dna"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    characteristic_slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    
    affinity_value: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.5000"))
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=Decimal("0.000"))
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("affinity_value >= 0.0 AND affinity_value <= 1.0", name="ck_dna_affinity_range"),
        CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_dna_confidence_range"),
        UniqueConstraint("user_id", "characteristic_slug", name="uq_dna_user_char"),
    )


class UserCategoryProfile(TimestampMixin, Base):
    """Broad category exposure and fatigue tracking."""
    __tablename__ = "user_category_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    exposure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    affinity_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.5000"))
    fatigue_level: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False, default=Decimal("0.0000"))
    
    last_experienced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "category_id", name="uq_ucprofile_user_cat"),
    )

    category: Mapped[Category] = relationship("Category", lazy="select")  # type: ignore[name-defined]

    @property
    def category_name(self) -> str | None:
        return self.category.name if self.category else None

# Late imports to break circular refs
from app.models.catalog import Category
