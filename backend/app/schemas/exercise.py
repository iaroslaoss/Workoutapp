from typing import Literal

from pydantic import BaseModel, Field, HttpUrl

from app.schemas.common import ORMModel, TempoMixin


class ExerciseBase(TempoMixin):
    name: str = Field(min_length=1, max_length=255)
    category: str
    equipment: str = Field(min_length=1, max_length=255)
    muscle_group: str = Field(min_length=1, max_length=255)
    default_tempo: str
    description: str = Field(min_length=1)
    video_url: HttpUrl | None = None


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(TempoMixin, BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = None
    equipment: str | None = Field(default=None, min_length=1, max_length=255)
    muscle_group: str | None = Field(default=None, min_length=1, max_length=255)
    default_tempo: str | None = None
    description: str | None = Field(default=None, min_length=1)
    video_url: HttpUrl | None = None


class ExerciseRead(ORMModel):
    id: str
    name: str
    category: str
    equipment: str
    muscle_group: str
    default_tempo: str
    description: str
    video_url: str | None
    created_by_trainer_id: str | None


class ExerciseCatalogResponse(BaseModel):
    items: list[ExerciseRead]
    total: int
    page: int
    page_size: int
    total_pages: int


class ExerciseFilterMetaResponse(BaseModel):
    categories: list[str]
    equipments: list[str]
    muscle_groups: list[str]


class ExerciseSuggestRequest(BaseModel):
    goal: Literal["strength", "hypertrophy", "fat_loss", "conditioning", "general_fitness"] = "general_fitness"
    session_focus: Literal["full_body", "push", "pull", "legs", "core", "conditioning"] = "full_body"
    available_equipment: list[str] | None = None
    limit: int = Field(default=6, ge=3, le=12)


class ExerciseSuggestion(BaseModel):
    exercise_id: str
    name: str
    category: str
    equipment: str
    muscle_group: str
    reason: str
    sets: int
    reps: str
    target_rpe: int | None
    rest_seconds: int | None


class ExerciseSuggestResponse(BaseModel):
    goal: str
    session_focus: str
    suggestions: list[ExerciseSuggestion]
