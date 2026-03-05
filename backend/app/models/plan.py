import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PlanTemplate(Base):
    __tablename__ = "plan_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trainer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    weeks_count: Mapped[int] = mapped_column(Integer, nullable=False)

    trainer = relationship("User", back_populates="plans")
    days = relationship("PlanDay", back_populates="plan_template", cascade="all, delete-orphan")


class PlanDay(Base):
    __tablename__ = "plan_days"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plan_templates.id", ondelete="CASCADE"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_name: Mapped[str] = mapped_column(String(50), nullable=False)

    plan_template = relationship("PlanTemplate", back_populates="days")
    exercises = relationship("PlanExercise", back_populates="plan_day", cascade="all, delete-orphan")

    __table_args__ = (CheckConstraint("week_number >= 1", name="ck_plan_days_week_positive"),)


class PlanExercise(Base):
    __tablename__ = "plan_exercises"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_day_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plan_days.id", ondelete="CASCADE"), nullable=False)
    exercise_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[str] = mapped_column(String(50), nullable=False)
    rpe: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    rest_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tempo: Mapped[str | None] = mapped_column(String(31), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    plan_day = relationship("PlanDay", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="plan_exercises")

    __table_args__ = (CheckConstraint("rpe IS NULL OR (rpe >= 1 AND rpe <= 10)", name="ck_plan_exercises_rpe_range"),)
