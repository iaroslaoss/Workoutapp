"""initial schema

Revision ID: 20260305_0001
Revises:
Create Date: 2026-03-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260305_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
            CREATE TYPE user_role AS ENUM ('trainer', 'admin');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'exercise_category') THEN
            CREATE TYPE exercise_category AS ENUM ('push', 'pull', 'legs', 'core', 'cardio', 'other');
        END IF;
    END
    $$;
    """)

    user_role = postgresql.ENUM("trainer", "admin", name="user_role", create_type=False)
    exercise_category = postgresql.ENUM("push", "pull", "legs", "core", "cardio", "other", name="exercise_category", create_type=False)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "clients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trainer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", exercise_category, nullable=False),
        sa.Column("equipment", sa.String(255), nullable=False),
        sa.Column("muscle_group", sa.String(255), nullable=False),
        sa.Column("default_tempo", sa.String(31), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column(
            "created_by_trainer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_exercises_name", "exercises", ["name"], unique=False)

    op.create_table(
        "plan_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("trainer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("weeks_count", sa.Integer(), nullable=False),
    )

    op.create_table(
        "plan_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "plan_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("week_number", sa.Integer(), nullable=False),
        sa.Column("day_name", sa.String(50), nullable=False),
        sa.CheckConstraint("week_number >= 1", name="ck_plan_days_week_positive"),
    )

    op.create_table(
        "plan_exercises",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "plan_day_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_days.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "exercise_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("exercises.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("sets", sa.Integer(), nullable=False),
        sa.Column("reps", sa.String(50), nullable=False),
        sa.Column("rpe", sa.Integer(), nullable=True),
        sa.Column("weight", sa.Numeric(8, 2), nullable=True),
        sa.Column("rest_seconds", sa.Integer(), nullable=True),
        sa.Column("tempo", sa.String(31), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.CheckConstraint("rpe IS NULL OR (rpe >= 1 AND rpe <= 10)", name="ck_plan_exercises_rpe_range"),
    )

    op.create_table(
        "assigned_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "client_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "plan_template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plan_templates.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_table("assigned_plans")
    op.drop_table("plan_exercises")
    op.drop_table("plan_days")
    op.drop_table("plan_templates")
    op.drop_index("ix_exercises_name", table_name="exercises")
    op.drop_table("exercises")
    op.drop_table("clients")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS exercise_category")
    op.execute("DROP TYPE IF EXISTS user_role")
