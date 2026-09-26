"""
Migration 0002 — Skill metadata expansion + new product entities.

New tables
----------
challenges           – Weekend quest challenges per skill
ratings              – Multi-dimensional post-experience rating (replaces feedback)
skill_dna            – Per-user, per-characteristic DNA values
user_category_profiles – Per-user, per-category affinity + fatigue
lockin_sessions      – LOCK IN deep-learning sessions
mix_candidates       – Detected cross-skill mix opportunities

Skill column additions
----------------------
environment, social_context, physical_demand, cost_level,
output_type, characteristic_tags
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_skill_meta_dna_lockin"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Expand skills table ───────────────────────────────────────────────
    op.add_column("skills", sa.Column("environment", sa.String(80), nullable=True))
    op.add_column("skills", sa.Column("social_context", sa.String(20), nullable=True))
    op.add_column("skills", sa.Column("physical_demand", sa.String(20), nullable=True))
    op.add_column("skills", sa.Column("cost_level", sa.String(20), nullable=True))
    op.add_column("skills", sa.Column("output_type", sa.String(80), nullable=True))
    # Comma-separated characteristic tags (for fast search / DNA matching)
    op.add_column("skills", sa.Column("characteristic_tags", sa.Text(), nullable=True))
    op.add_column("skills", sa.Column("subcategory", sa.String(80), nullable=True))
    op.add_column("skills", sa.Column("skill_type", sa.String(40), nullable=True))

    # ── challenges ────────────────────────────────────────────────────────
    op.create_table(
        "challenges",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("subtitle", sa.String(300), nullable=True),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("learn_content", sa.Text(), nullable=True),
        sa.Column("do_content", sa.Text(), nullable=False),
        sa.Column("finish_criteria", sa.Text(), nullable=False),
        sa.Column("stretch_goal", sa.Text(), nullable=True),
        sa.Column("why_this_matters", sa.Text(), nullable=True),
        sa.Column("resources", sa.Text(), nullable=True),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="120"),
        sa.Column("difficulty_level", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("catalog_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("difficulty_level BETWEEN 1 AND 5", name="ck_challenge_difficulty"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_challenges_skill_id", "challenges", ["skill_id"])
    op.create_index("ix_challenges_is_active", "challenges", ["is_active"])

    # ── ratings (multi-dimensional, replaces simple feedback) ─────────────
    op.create_table(
        "ratings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("quest_attempt_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("challenge_id", sa.UUID(), nullable=True),
        # ── Pre-experience signal ──
        sa.Column("pre_interest", sa.Integer(), nullable=True),    # 1-10 interest BEFORE
        # ── Post-experience signals ──
        sa.Column("enjoyment", sa.Integer(), nullable=False),      # 1-10
        sa.Column("curiosity", sa.Integer(), nullable=False),      # 1-10 want more
        sa.Column("difficulty_felt", sa.Integer(), nullable=True), # 1-10
        sa.Column("would_repeat", sa.String(10), nullable=False),  # yes/maybe/no
        sa.Column("deep_dive_interest", sa.Integer(), nullable=False),  # 1-10
        sa.Column("standout_moment", sa.Text(), nullable=True),    # what stood out
        sa.Column("friction_notes", sa.Text(), nullable=True),     # what was hard/annoying
        # ── AI-extractable text ──
        sa.Column("free_text", sa.Text(), nullable=True),
        # ── Computed signals (set by backend after rating submitted) ──
        sa.Column("composite_score", sa.Numeric(4, 2), nullable=True),
        sa.Column("affinity_signal", sa.Numeric(4, 3), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("enjoyment BETWEEN 1 AND 10", name="ck_rating_enjoyment"),
        sa.CheckConstraint("curiosity BETWEEN 1 AND 10", name="ck_rating_curiosity"),
        sa.CheckConstraint("pre_interest BETWEEN 1 AND 10", name="ck_rating_pre_interest"),
        sa.CheckConstraint("deep_dive_interest BETWEEN 1 AND 10", name="ck_rating_deep_dive"),
        sa.CheckConstraint("difficulty_felt BETWEEN 1 AND 10", name="ck_rating_difficulty"),
        sa.CheckConstraint("would_repeat IN ('yes','maybe','no')", name="ck_rating_repeat"),
        sa.ForeignKeyConstraint(["challenge_id"], ["challenges.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["quest_attempt_id"], ["quest_attempts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quest_attempt_id", name="uq_rating_quest_attempt"),
    )
    op.create_index("ix_ratings_user_id", "ratings", ["user_id"])
    op.create_index("ix_ratings_skill_id", "ratings", ["skill_id"])
    op.create_index("ix_ratings_quest_attempt_id", "ratings", ["quest_attempt_id"])

    # ── skill_dna ─────────────────────────────────────────────────────────
    # One row per (user, characteristic_slug) — updated after each rating.
    op.create_table(
        "skill_dna",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("characteristic_slug", sa.String(80), nullable=False),
        # 0.0–1.0 affinity score for this characteristic
        sa.Column("affinity_value", sa.Numeric(5, 4), nullable=False, server_default="0.5000"),
        # 0.0–1.0 confidence (grows with sample size)
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.000"),
        # Number of experiences that contributed to this value
        sa.Column("sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("affinity_value >= 0.0 AND affinity_value <= 1.0", name="ck_dna_affinity_range"),
        sa.CheckConstraint("confidence >= 0.0 AND confidence <= 1.0", name="ck_dna_confidence_range"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "characteristic_slug", name="uq_dna_user_char"),
    )
    op.create_index("ix_skill_dna_user_id", "skill_dna", ["user_id"])
    op.create_index("ix_skill_dna_characteristic_slug", "skill_dna", ["characteristic_slug"])

    # ── user_category_profiles ────────────────────────────────────────────
    # Tracks per-category affinity, exposure count, and fatigue.
    op.create_table(
        "user_category_profiles",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("exposure_count", sa.Integer(), nullable=False, server_default="0"),
        # 0.0–1.0 rolling affinity (EMA of composite scores)
        sa.Column("affinity_score", sa.Numeric(5, 4), nullable=False, server_default="0.5000"),
        # 0.0–1.0 fatigue (high = recently over-exposed, decays over time)
        sa.Column("fatigue_level", sa.Numeric(5, 4), nullable=False, server_default="0.0000"),
        sa.Column("last_experienced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "category_id", name="uq_ucprofile_user_cat"),
    )
    op.create_index("ix_user_category_profiles_user_id", "user_category_profiles", ["user_id"])
    op.create_index("ix_user_category_profiles_category_id", "user_category_profiles", ["category_id"])

    # ── lockin_sessions ───────────────────────────────────────────────────
    op.create_table(
        "lockin_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("skill_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        # 0 = foundation, 1 = intermediate, 2 = project, 3 = advanced
        sa.Column("progression_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unlock_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('active','completed','unlocked')",
            name="ck_lockin_status",
        ),
        sa.CheckConstraint("progression_level >= 0 AND progression_level <= 4", name="ck_lockin_progression"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lockin_sessions_user_id", "lockin_sessions", ["user_id"])
    op.create_index("ix_lockin_sessions_status", "lockin_sessions", ["status"])

    # ── mix_candidates ────────────────────────────────────────────────────
    # Detected cross-skill mix opportunities for MIX MODE.
    op.create_table(
        "mix_candidates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("skill_a_id", sa.UUID(), nullable=False),
        sa.Column("skill_b_id", sa.UUID(), nullable=False),
        # The skill that represents their intersection
        sa.Column("result_skill_id", sa.UUID(), nullable=True),
        sa.Column("mix_label", sa.String(200), nullable=False),
        sa.Column("mix_explanation", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("is_presented", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("skill_a_id <> skill_b_id", name="ck_mix_no_self"),
        sa.ForeignKeyConstraint(["result_skill_id"], ["skills.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["skill_a_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_b_id"], ["skills.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "skill_a_id", "skill_b_id", name="uq_mix_user_skills"),
    )
    op.create_index("ix_mix_candidates_user_id", "mix_candidates", ["user_id"])

    # ── quest_attempts: link challenge ─────────────────────────────────────
    op.add_column(
        "quest_attempts",
        sa.Column("challenge_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_questattempt_challenge",
        "quest_attempts",
        "challenges",
        ["challenge_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── recommendations: mix_mode flag ────────────────────────────────────
    op.add_column(
        "recommendations",
        sa.Column("is_mix_recommendation", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "recommendations",
        sa.Column("ai_explanation", sa.Text(), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("confidence_score", sa.Numeric(4, 3), nullable=True),
    )
    op.add_column(
        "recommendations",
        sa.Column("mix_candidate_id", sa.UUID(), nullable=True),
    )

    # ── users: mode + mix_enabled ─────────────────────────────────────────
    op.add_column(
        "users",
        sa.Column("exploration_mode", sa.String(20), nullable=False, server_default="explore"),
    )
    op.add_column(
        "users",
        sa.Column("mix_mode_enabled", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "users",
        sa.Column("mix_threshold", sa.Integer(), nullable=False, server_default="8"),
    )


def downgrade() -> None:
    # Remove columns from users
    op.drop_column("users", "mix_threshold")
    op.drop_column("users", "mix_mode_enabled")
    op.drop_column("users", "exploration_mode")

    # Remove columns from recommendations
    op.drop_column("recommendations", "mix_candidate_id")
    op.drop_column("recommendations", "confidence_score")
    op.drop_column("recommendations", "ai_explanation")
    op.drop_column("recommendations", "is_mix_recommendation")

    # Remove challenge_id from quest_attempts
    op.drop_constraint("fk_questattempt_challenge", "quest_attempts", type_="foreignkey")
    op.drop_column("quest_attempts", "challenge_id")

    # Drop new tables
    op.drop_table("mix_candidates")
    op.drop_table("lockin_sessions")
    op.drop_table("user_category_profiles")
    op.drop_table("skill_dna")
    op.drop_table("ratings")
    op.drop_table("challenges")

    # Remove skill columns
    for col in ["skill_type", "subcategory", "characteristic_tags", "output_type",
                "cost_level", "physical_demand", "social_context", "environment"]:
        op.drop_column("skills", col)
