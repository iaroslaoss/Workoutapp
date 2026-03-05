from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel, TempoMixin


class PlanTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    weeks_count: int = Field(ge=1, le=52)


class PlanTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    weeks_count: int | None = Field(default=None, ge=1, le=52)


class PlanTemplateRead(ORMModel):
    id: UUID
    trainer_id: UUID
    name: str
    description: str
    weeks_count: int


class PlanDayCreate(BaseModel):
    week_number: int = Field(ge=1)
    day_name: str = Field(min_length=1, max_length=50)


class PlanDayUpdate(BaseModel):
    week_number: int | None = Field(default=None, ge=1)
    day_name: str | None = Field(default=None, min_length=1, max_length=50)


class PlanDayRead(ORMModel):
    id: str
    plan_template_id: str
    week_number: int
    day_name: str


class PlanExerciseCreate(TempoMixin):
    exercise_id: UUID
    sets: int = Field(ge=1)
    reps: str = Field(min_length=1, max_length=50)
    rpe: int | None = Field(default=None, ge=1, le=10)
    weight: Decimal | None = None
    rest_seconds: int | None = Field(default=None, ge=0)
    tempo: str | None = None
    notes: str | None = None


class PlanExerciseUpdate(TempoMixin, BaseModel):
    exercise_id: UUID | None = None
    sets: int | None = Field(default=None, ge=1)
    reps: str | None = Field(default=None, min_length=1, max_length=50)
    rpe: int | None = Field(default=None, ge=1, le=10)
    weight: Decimal | None = None
    rest_seconds: int | None = Field(default=None, ge=0)
    tempo: str | None = None
    notes: str | None = None


class PlanExerciseRead(ORMModel):
    id: str
    plan_day_id: str
    exercise_id: str
    sets: int
    reps: str
    rpe: int | None
    weight: Decimal | None
    rest_seconds: int | None
    tempo: str | None
    notes: str | None


class AssignedPlanCreate(BaseModel):
    client_id: UUID
    plan_template_id: UUID
    start_date: date
    active: bool = True


class AssignedPlanRead(ORMModel):
    id: str
    client_id: str
    plan_template_id: str
    start_date: date
    active: bool


class AssignmentSummary(BaseModel):
    assignment: AssignedPlanRead | None
    plan: PlanTemplateRead | None


class ClientPlanExerciseView(BaseModel):
    id: str
    exercise_name: str
    sets: int
    reps: str
    rpe: int | None
    weight: Decimal | None
    rest_seconds: int | None
    tempo: str
    notes: str | None


class ClientPlanDayView(BaseModel):
    id: str
    week_number: int
    day_name: str
    exercises: list[ClientPlanExerciseView]


class ClientPlanView(BaseModel):
    client_id: str
    plan_template_id: str
    plan_name: str
    start_date: date
    active: bool
    days: list[ClientPlanDayView]


class DuplicateDayRequest(BaseModel):
    source_day_id: UUID
    target_day_id: UUID


class DuplicatePlanRequest(BaseModel):
    name: str | None = None


class StarterPlanSuggestionRead(BaseModel):
    slug: str
    name: str
    description: str
    weeks_count: int
    sessions_per_week: int
    goal: str


class StarterPlanImportResponse(BaseModel):
    plan: PlanTemplateRead
    days_created: int
    exercises_created: int
    missing_exercises: list[str]
