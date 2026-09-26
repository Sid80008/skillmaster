"""Initial schema – all tables

Revision ID: 0001_initial
Revises: 
Create Date: 2026-09-26
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_username", "users", ["username"])

    # ── user_constraints ──────────────────────────────────────────────────
    op.create_table(
        "user_constraints",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("physical_restrictions", sa.Text(), nullable=True),
        sa.Column("equipment_exclusions", sa.Text(), nullable=True),
        sa.Column("max_session_minutes", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_user_constraints_user_id", "user_constraints", ["user_id"])

    # ── categories ────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_categories_slug", "categories", ["slug"])

    # ── activity_families ─────────────────────────────────────────────────
    op.create_table(
        "activity_families",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_activity_families_category_id", "activity_families", ["category_id"])
    op.create_index("ix_activity_families_slug", "activity_families", ["slug"])

    # ── characteristics ───────────────────────────────────────────────────
    op.create_table(
        "characteristics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_characteristics_slug", "characteristics", ["slug"])

    # ── skills ────────────────────────────────────────────────────────────
    op.create_table(
        "skills",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("activity_family_id", sa.UUID(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("catalog_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("physical_restriction_tags", sa.Text(), nullable=True),
        sa.Column("required_equipment_tags", sa.Text(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("difficulty_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("estimated_duration_minutes > 0", name="ck_skill_positive_duration"),
        sa.CheckConstraint("difficulty_level BETWEEN 1 AND 10", name="ck_skill_difficulty_range"),
        sa.ForeignKeyConstraint(["activity_family_id"], ["activity_families.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", "catalog_version", name="uq_skill_slug_version"),
    )
    op.create_index("ix_skills_activity_family_id", "skills", ["activity_family_id"])
    op.create_index("ix_skills_slug", "skills", ["slug"])

    # ── skill_characteristics ─────────────────────────────────────────────
    op.create_table(
        "skill_characteristics",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("characteristic_id", sa.UUID(), nullable=False),
        sa.Column("value", sa.Numeric(5, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("value >= 0.0 AND value <= 1.0", name="ck_skillchar_value_range"),
        sa.ForeignKeyConstraint(["characteristic_id"], ["characteristics.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "characteristic_id", name="uq_skillchar_skill_char"),
    )
    op.create_index("ix_skill_characteristics_characteristic_id", "skill_characteristics", ["characteristic_id"])
    op.create_index("ix_skill_characteristics_skill_id", "skill_characteristics", ["skill_id"])

    # ── skill_relationships ───────────────────────────────────────────────
    op.create_table(
        "skill_relationships",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("from_skill_id", sa.UUID(), nullable=False),
        sa.Column("to_skill_id", sa.UUID(), nullable=False),
        sa.Column("relationship_type", sa.String(40), nullable=False),
        sa.Column("strength", sa.Numeric(4, 3), nullable=False, server_default="1.000"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("from_skill_id <> to_skill_id", name="ck_skillrel_no_self_reference"),
        sa.ForeignKeyConstraint(["from_skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_skill_id"], ["skills.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("from_skill_id", "to_skill_id", "relationship_type", name="uq_skillrel_unique"),
    )
    op.create_index("ix_skill_relationships_from_skill_id", "skill_relationships", ["from_skill_id"])
    op.create_index("ix_skill_relationships_relationship_type", "skill_relationships", ["relationship_type"])
    op.create_index("ix_skill_relationships_to_skill_id", "skill_relationships", ["to_skill_id"])

    # ── quests ────────────────────────────────────────────────────────────
    op.create_table(
        "quests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("catalog_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("skill_id", "catalog_version", name="uq_quest_skill_version"),
    )
    op.create_index("ix_quests_skill_id", "quests", ["skill_id"])

    # ── quest_attempts ────────────────────────────────────────────────────
    op.create_table(
        "quest_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("quest_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("skill_catalog_version", sa.Integer(), nullable=False),
        sa.Column("activity_family_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandoned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("abandonment_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending','active','completed','abandoned','cancelled')",
            name="ck_questattempt_valid_status",
        ),
        sa.ForeignKeyConstraint(["activity_family_id"], ["activity_families.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quest_id"], ["quests.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_quest_attempts_activity_family_id", "quest_attempts", ["activity_family_id"])
    op.create_index("ix_quest_attempts_quest_id", "quest_attempts", ["quest_id"])
    op.create_index("ix_quest_attempts_skill_id", "quest_attempts", ["skill_id"])
    op.create_index("ix_quest_attempts_status", "quest_attempts", ["status"])
    op.create_index("ix_quest_attempts_user_id", "quest_attempts", ["user_id"])

    # ── recommendations ───────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("presented_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("selected_skill_id", sa.UUID(), nullable=True),
        sa.Column("resulting_quest_attempt_id", sa.UUID(), nullable=True),
        sa.Column("generation_context", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending','presented','accepted','rejected','expired')",
            name="ck_recommendation_valid_status",
        ),
        sa.ForeignKeyConstraint(["resulting_quest_attempt_id"], ["quest_attempts.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["selected_skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recommendations_selected_skill_id", "recommendations", ["selected_skill_id"])
    op.create_index("ix_recommendations_status", "recommendations", ["status"])
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])

    # ── recommendation_candidates ─────────────────────────────────────────
    op.create_table(
        "recommendation_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("recommendation_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("skill_catalog_version", sa.Integer(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(5, 4), nullable=False),
        sa.Column("novelty_category", sa.String(40), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rank > 0", name="ck_reccandidate_positive_rank"),
        sa.CheckConstraint("score >= 0.0 AND score <= 1.0", name="ck_reccandidate_score_range"),
        sa.ForeignKeyConstraint(["recommendation_id"], ["recommendations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("recommendation_id", "skill_id", name="uq_reccandidate_recommendation_skill"),
    )
    op.create_index("ix_recommendation_candidates_novelty_category", "recommendation_candidates", ["novelty_category"])
    op.create_index("ix_recommendation_candidates_recommendation_id", "recommendation_candidates", ["recommendation_id"])
    op.create_index("ix_recommendation_candidates_skill_id", "recommendation_candidates", ["skill_id"])

    # ── feedbacks ─────────────────────────────────────────────────────────
    op.create_table(
        "feedbacks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("quest_attempt_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("enjoyment_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.String(500), nullable=True),
        sa.Column("would_repeat", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("rating BETWEEN 1 AND 5", name="ck_feedback_rating_range"),
        sa.CheckConstraint("enjoyment_score >= 0.0 AND enjoyment_score <= 1.0", name="ck_feedback_enjoyment_range"),
        sa.ForeignKeyConstraint(["quest_attempt_id"], ["quest_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quest_attempt_id", name="uq_feedback_quest_attempt"),
    )
    op.create_index("ix_feedbacks_quest_attempt_id", "feedbacks", ["quest_attempt_id"])
    op.create_index("ix_feedbacks_user_id", "feedbacks", ["user_id"])


def downgrade() -> None:
    op.drop_table("feedbacks")
    op.drop_table("recommendation_candidates")
    op.drop_table("recommendations")
    op.drop_table("quest_attempts")
    op.drop_table("quests")
    op.drop_table("skill_relationships")
    op.drop_table("skill_characteristics")
    op.drop_table("skills")
    op.drop_table("characteristics")
    op.drop_table("activity_families")
    op.drop_table("categories")
    op.drop_table("user_constraints")
    op.drop_table("users")
