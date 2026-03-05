import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    assigned_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assigned_plans.id", ondelete="SET NULL"), nullable=True
    )
    logged_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(Enum("completed", "missed", name="workout_log_status"), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client = relationship("Client")
    assigned_plan = relationship("AssignedPlan")
    set_logs = relationship("SetLog", back_populates="workout_log", cascade="all, delete-orphan")


class SetLog(Base):
    __tablename__ = "set_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workout_log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workout_logs.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    set_number: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_rpe: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    workout_log = relationship("WorkoutLog", back_populates="set_logs")
    exercise = relationship("Exercise")

    __table_args__ = (UniqueConstraint("workout_log_id", "exercise_id", "set_number", name="uq_set_logs_workout_exercise_set"),)


class DailyCheckIn(Base):
    __tablename__ = "daily_checkins"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    sleep_score: Mapped[int] = mapped_column(Integer, nullable=False)
    stress_level: Mapped[int] = mapped_column(Integer, nullable=False)
    soreness_level: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client = relationship("Client")

    __table_args__ = (UniqueConstraint("client_id", "check_in_date", name="uq_daily_checkins_client_date"),)
