"""add workout logs and daily checkins

Revision ID: 20260305_0002
Revises: 20260305_0001
Create Date: 2026-03-05
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "20260305_0002"
down_revision: Union[str, Sequence[str], None] = "20260305_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'workout_log_status') THEN
                CREATE TYPE workout_log_status AS ENUM ('completed', 'missed');
            END IF;
        END
        $$;
        """
    )

    workout_log_status = postgresql.ENUM("completed", "missed", name="workout_log_status", create_type=False)

    op.create_table(
        "workout_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "assigned_plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("assigned_plans.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("logged_date", sa.Date(), nullable=False),
        sa.Column("status", workout_log_status, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_workout_logs_client_id", "workout_logs", ["client_id"], unique=False)
    op.create_index("ix_workout_logs_logged_date", "workout_logs", ["logged_date"], unique=False)
    op.create_index("ix_workout_logs_status", "workout_logs", ["status"], unique=False)

    op.create_table(
        "set_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("workout_log_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exercise_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("actual_reps", sa.Integer(), nullable=False),
        sa.Column("actual_weight", sa.Float(), nullable=True),
        sa.Column("actual_rpe", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("workout_log_id", "exercise_id", "set_number", name="uq_set_logs_workout_exercise_set"),
    )
    op.create_index("ix_set_logs_workout_log_id", "set_logs", ["workout_log_id"], unique=False)
    op.create_index("ix_set_logs_exercise_id", "set_logs", ["exercise_id"], unique=False)

    op.create_table(
        "daily_checkins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("client_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("clients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_in_date", sa.Date(), nullable=False),
        sa.Column("sleep_score", sa.Integer(), nullable=False),
        sa.Column("stress_level", sa.Integer(), nullable=False),
        sa.Column("soreness_level", sa.Integer(), nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("client_id", "check_in_date", name="uq_daily_checkins_client_date"),
    )
    op.create_index("ix_daily_checkins_client_id", "daily_checkins", ["client_id"], unique=False)
    op.create_index("ix_daily_checkins_check_in_date", "daily_checkins", ["check_in_date"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_checkins_check_in_date", table_name="daily_checkins")
    op.drop_index("ix_daily_checkins_client_id", table_name="daily_checkins")
    op.drop_table("daily_checkins")

    op.drop_index("ix_set_logs_exercise_id", table_name="set_logs")
    op.drop_index("ix_set_logs_workout_log_id", table_name="set_logs")
    op.drop_table("set_logs")

    op.drop_index("ix_workout_logs_status", table_name="workout_logs")
    op.drop_index("ix_workout_logs_logged_date", table_name="workout_logs")
    op.drop_index("ix_workout_logs_client_id", table_name="workout_logs")
    op.drop_table("workout_logs")

    op.execute("DROP TYPE IF EXISTS workout_log_status")
