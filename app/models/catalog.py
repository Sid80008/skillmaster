"""
Catalog ORM models: Category, ActivityFamily, Characteristic, Skill,
SkillCharacteristic, SkillRelationship.

Catalog entities are versioned / immutable once published.  They may be
deprecated but never silently mutated in a way that would retroactively
change the meaning of historical QuestAttempts or Recommendations.

Versioning strategy
-------------------
* Each catalog entity carries a ``catalog_version`` integer column.
* When a skill is substantially updated, a NEW row is created with
  a higher ``catalog_version`` (the old row is marked ``is_active=False``).
* Historical QuestAttempts reference the *specific* skill row they were
  originally given – snapshots via ``skill_catalog_version`` on the attempt.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
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


# ─────────────────────────────────────────────────────────────────────────────
# Category
# ─────────────────────────────────────────────────────────────────────────────


class Category(TimestampMixin, Base):
    """
    Top-level grouping of activity families.

    Examples: Outdoor, Indoor, Aquatic, Aerial, Creative, Mindful.
    """

    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # ── Relationships ─────────────────────────────────────────────────────
    activity_families: Mapped[list[ActivityFamily]] = relationship(
        "ActivityFamily", back_populates="category", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Category slug={self.slug!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# ActivityFamily
# ─────────────────────────────────────────────────────────────────────────────


class ActivityFamily(TimestampMixin, Base):
    """
    A cluster of closely related skills sharing a common experiential core.

    Example: "Rock Climbing" is an activity family containing skills like
    "Top-rope climbing", "Bouldering", "Lead climbing", etc.

    Experiencing ANY skill in a family counts as experiencing that family
    for novelty / variety calculations.
    """

    __tablename__ = "activity_families"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ─────────────────────────────────────────────────────
    category: Mapped[Category] = relationship(
        "Category", back_populates="activity_families"
    )
    skills: Mapped[list[Skill]] = relationship(
        "Skill", back_populates="activity_family", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<ActivityFamily slug={self.slug!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Characteristic
# ─────────────────────────────────────────────────────────────────────────────


class Characteristic(TimestampMixin, Base):
    """
    A named dimension along which skills vary.

    Examples: intensity, social_context, environment, risk_level,
    required_equipment, physical_demand, creative_expression.

    Characteristics drive the structured distance/novelty model.
    """

    __tablename__ = "characteristics"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(80), nullable=False, unique=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ─────────────────────────────────────────────────────
    skill_characteristics: Mapped[list[SkillCharacteristic]] = relationship(
        "SkillCharacteristic", back_populates="characteristic", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Characteristic slug={self.slug!r}>"


# ─────────────────────────────────────────────────────────────────────────────
# Skill
# ─────────────────────────────────────────────────────────────────────────────


class Skill(TimestampMixin, Base):
    """
    A single, concrete learnable/explorable skill.

    Versioning
    ----------
    * ``catalog_version`` increments when the canonical definition changes.
    * When a new version is created, the old row's ``is_active`` is set to
      False; the new row gets a new primary-key UUID but the same ``slug``.
    * ``is_active=True`` means "eligible for new recommendations".
    * Historical quest attempts always reference the UUID they were given —
      even if that version is now inactive.
    """

    __tablename__ = "skills"
    __table_args__ = (
        CheckConstraint(
            "estimated_duration_minutes > 0",
            name="ck_skill_positive_duration",
        ),
        CheckConstraint(
            "difficulty_level BETWEEN 1 AND 10",
            name="ck_skill_difficulty_range",
        ),
        UniqueConstraint("slug", "catalog_version", name="uq_skill_slug_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    activity_family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("activity_families.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    catalog_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ── Eligibility tags ──────────────────────────────────────────────────
    # Comma-separated physical restriction tags that disqualify this skill.
    physical_restriction_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Comma-separated equipment tags this skill requires.
    required_equipment_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Minimum session length in minutes.
    estimated_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30
    )
    # 1–10 difficulty scale.
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # ── Rich metadata (Phase 2) ───────────────────────────────────────────
    # indoor / outdoor / both
    environment: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # solo / social / either
    social_context: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # low / medium / high
    physical_demand: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # free / low / medium / high
    cost_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # e.g. artifact / performance / knowledge / service / digital
    output_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # Comma-separated characteristic tags for DNA matching.
    # e.g. "hands-on,creative,visual,experimental,technical"
    characteristic_tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    # e.g. "Visual Arts", "Electronics", etc.
    subcategory: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # creative / technical / practical / physical / intellectual / social
    skill_type: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    activity_family: Mapped[ActivityFamily] = relationship(
        "ActivityFamily", back_populates="skills"
    )
    skill_characteristics: Mapped[list[SkillCharacteristic]] = relationship(
        "SkillCharacteristic", back_populates="skill", lazy="select"
    )
    # outgoing relationships (this skill → other skills)
    outgoing_relationships: Mapped[list[SkillRelationship]] = relationship(
        "SkillRelationship",
        foreign_keys="[SkillRelationship.from_skill_id]",
        back_populates="from_skill",
        lazy="select",
    )
    # incoming relationships (other skills → this skill)
    incoming_relationships: Mapped[list[SkillRelationship]] = relationship(
        "SkillRelationship",
        foreign_keys="[SkillRelationship.to_skill_id]",
        back_populates="to_skill",
        lazy="select",
    )

    def physical_restriction_tag_set(self) -> frozenset[str]:
        if not self.physical_restriction_tags:
            return frozenset()
        return frozenset(
            t.strip() for t in self.physical_restriction_tags.split(",") if t.strip()
        )

    def required_equipment_tag_set(self) -> frozenset[str]:
        if not self.required_equipment_tags:
            return frozenset()
        return frozenset(
            t.strip() for t in self.required_equipment_tags.split(",") if t.strip()
        )

    def __repr__(self) -> str:
        return f"<Skill slug={self.slug!r} v{self.catalog_version}>"


# ─────────────────────────────────────────────────────────────────────────────
# SkillCharacteristic
# ─────────────────────────────────────────────────────────────────────────────


class SkillCharacteristic(TimestampMixin, Base):
    """
    Assigns a characteristic value to a specific skill.

    ``value`` is a numeric score 0.0–1.0 for that characteristic dimension.
    This enables deterministic distance calculations between skills.
    """

    __tablename__ = "skill_characteristics"
    __table_args__ = (
        UniqueConstraint(
            "skill_id", "characteristic_id", name="uq_skillchar_skill_char"
        ),
        CheckConstraint(
            "value >= 0.0 AND value <= 1.0", name="ck_skillchar_value_range"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    characteristic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("characteristics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────────────────
    skill: Mapped[Skill] = relationship("Skill", back_populates="skill_characteristics")
    characteristic: Mapped[Characteristic] = relationship(
        "Characteristic", back_populates="skill_characteristics"
    )

    def __repr__(self) -> str:
        return f"<SkillCharacteristic skill={self.skill_id} char={self.characteristic_id} val={self.value}>"


# ─────────────────────────────────────────────────────────────────────────────
# SkillRelationship
# ─────────────────────────────────────────────────────────────────────────────


class SkillRelationship(TimestampMixin, Base):
    """
    Directed, typed relationship between two skills.

    Relationship types
    ------------------
    ``prerequisite``   – from_skill must be completed before to_skill.
    ``complementary``  – skills that pair well together experientially.
    ``progression``    – natural difficulty progression from → to.
    ``near_duplicate`` – skills so similar they count as the same experience.

    These relationships are used by the novelty engine to determine
    experiential neighborhoods.
    """

    __tablename__ = "skill_relationships"
    __table_args__ = (
        UniqueConstraint(
            "from_skill_id", "to_skill_id", "relationship_type",
            name="uq_skillrel_unique",
        ),
        CheckConstraint(
            "from_skill_id <> to_skill_id",
            name="ck_skillrel_no_self_reference",
        ),
    )

    VALID_TYPES = frozenset(
        {"prerequisite", "complementary", "progression", "near_duplicate"}
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=new_uuid, nullable=False
    )
    from_skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    to_skill_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[str] = mapped_column(
        String(40), nullable=False, index=True
    )
    strength: Mapped[Decimal] = mapped_column(
        Numeric(4, 3), nullable=False, default=Decimal("1.000")
    )

    # ── Relationships ─────────────────────────────────────────────────────
    from_skill: Mapped[Skill] = relationship(
        "Skill", foreign_keys=[from_skill_id], back_populates="outgoing_relationships"
    )
    to_skill: Mapped[Skill] = relationship(
        "Skill", foreign_keys=[to_skill_id], back_populates="incoming_relationships"
    )

    def __repr__(self) -> str:
        return (
            f"<SkillRelationship {self.from_skill_id}→{self.to_skill_id}"
            f" type={self.relationship_type!r}>"
        )
