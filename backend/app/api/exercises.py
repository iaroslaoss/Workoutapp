from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, distinct, func, or_, select
from sqlalchemy.orm import Session

from app.db.deps import get_current_user
from app.db.session import get_db
from app.models.exercise import Exercise
from app.models.user import User
from app.schemas.exercise import (
    ExerciseCatalogResponse,
    ExerciseCreate,
    ExerciseFilterMetaResponse,
    ExerciseRead,
    ExerciseSuggestRequest,
    ExerciseSuggestion,
    ExerciseSuggestResponse,
    ExerciseUpdate,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])

GOAL_CATEGORY_WEIGHTS: dict[str, dict[str, int]] = {
    "strength": {"push": 24, "pull": 24, "legs": 28, "core": 12, "cardio": 4, "other": 10},
    "hypertrophy": {"push": 26, "pull": 26, "legs": 26, "core": 10, "cardio": 3, "other": 8},
    "fat_loss": {"push": 14, "pull": 14, "legs": 16, "core": 18, "cardio": 28, "other": 14},
    "conditioning": {"push": 8, "pull": 8, "legs": 12, "core": 16, "cardio": 30, "other": 18},
    "general_fitness": {"push": 18, "pull": 18, "legs": 20, "core": 16, "cardio": 14, "other": 12},
}

FOCUS_CATEGORY_BONUS: dict[str, dict[str, int]] = {
    "full_body": {"push": 10, "pull": 10, "legs": 10, "core": 8, "cardio": 6, "other": 6},
    "push": {"push": 24, "pull": 4, "legs": 2, "core": 6, "cardio": 2, "other": 4},
    "pull": {"push": 4, "pull": 24, "legs": 2, "core": 6, "cardio": 2, "other": 4},
    "legs": {"push": 2, "pull": 2, "legs": 26, "core": 8, "cardio": 4, "other": 6},
    "core": {"push": 2, "pull": 2, "legs": 4, "core": 24, "cardio": 8, "other": 6},
    "conditioning": {"push": 2, "pull": 2, "legs": 6, "core": 10, "cardio": 24, "other": 14},
}

GOAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "strength": ("squat", "deadlift", "press", "row", "pull-up", "lunge", "thrust", "carry"),
    "hypertrophy": ("press", "row", "curl", "raise", "extension", "fly", "pulldown", "squat"),
    "fat_loss": ("interval", "carry", "sled", "battle rope", "burpee", "climber", "bike", "rower"),
    "conditioning": ("interval", "sprint", "bike", "rower", "treadmill", "stair", "rope", "slam"),
    "general_fitness": ("squat", "push", "pull", "lunge", "hinge", "core", "carry"),
}


def _visibility_filter(current_user: User):
    return or_(Exercise.created_by_trainer_id == None, Exercise.created_by_trainer_id == current_user.id)  # noqa: E711


def _build_filters(current_user: User, name: str | None, category: str | None, equipment: str | None, muscle_group: str | None):
    filters = [_visibility_filter(current_user)]
    if name:
        filters.append(Exercise.name.ilike(f"%{name}%"))
    if category:
        filters.append(Exercise.category == category)
    if equipment:
        filters.append(Exercise.equipment == equipment)
    if muscle_group:
        filters.append(Exercise.muscle_group == muscle_group)
    return filters


def _serialize_exercise(exercise: Exercise) -> ExerciseRead:
    return ExerciseRead(
        id=str(exercise.id),
        name=exercise.name,
        category=exercise.category,
        equipment=exercise.equipment,
        muscle_group=exercise.muscle_group,
        default_tempo=exercise.default_tempo,
        description=exercise.description,
        video_url=exercise.video_url,
        created_by_trainer_id=str(exercise.created_by_trainer_id) if exercise.created_by_trainer_id else None,
    )


def _prescription_for_goal(goal: str, category: str) -> tuple[int, str, int | None, int | None]:
    if goal == "strength":
        return (5 if category in {"push", "pull", "legs"} else 3, "4-6", 8, 150)
    if goal == "hypertrophy":
        return (4 if category in {"push", "pull", "legs"} else 3, "8-12", 8, 90)
    if goal == "fat_loss":
        if category == "cardio":
            return (4, "30-45 sec", 7, 45)
        return (3, "10-15", 7, 60)
    if goal == "conditioning":
        if category == "cardio":
            return (6, "20-40 sec", 7, 30)
        return (3, "8-12", 7, 60)
    if category == "cardio":
        return (3, "5-10 min", 6, 60)
    return (3, "8-12", 7, 75)


def _score_and_reason(exercise: Exercise, goal: str, session_focus: str, available_equipment: set[str] | None):
    base = GOAL_CATEGORY_WEIGHTS.get(goal, GOAL_CATEGORY_WEIGHTS["general_fitness"]).get(exercise.category, 0)
    focus = FOCUS_CATEGORY_BONUS.get(session_focus, FOCUS_CATEGORY_BONUS["full_body"]).get(exercise.category, 0)

    name_lower = exercise.name.lower()
    keyword_hits = sum(1 for token in GOAL_KEYWORDS.get(goal, ()) if token in name_lower)

    equipment_score = 0
    equipment_reason = None
    if available_equipment:
        if exercise.equipment in available_equipment:
            equipment_score = 14
            equipment_reason = f"Matches available equipment ({exercise.equipment})."
        elif exercise.equipment == "Bodyweight":
            equipment_score = 10
            equipment_reason = "Bodyweight option works with any setup."
        else:
            equipment_score = -25

    compound_bonus = 0
    if any(token in name_lower for token in ("squat", "deadlift", "press", "row", "pull-up", "lunge", "thrust")):
        compound_bonus = 8

    score = base + focus + keyword_hits * 4 + equipment_score + compound_bonus

    reasons: list[str] = []
    if focus >= 20:
        reasons.append(f"Strong fit for {session_focus.replace('_', ' ')} focus.")
    elif focus >= 8:
        reasons.append("Supports this session focus.")

    if base >= 22:
        reasons.append(f"High value for {goal.replace('_', ' ')} goal.")
    elif base >= 14:
        reasons.append(f"Useful for {goal.replace('_', ' ')} progression.")

    if keyword_hits > 0:
        reasons.append("Movement pattern aligns with goal priorities.")

    if equipment_reason:
        reasons.append(equipment_reason)

    if not reasons:
        reasons.append("Good general-purpose exercise for this session.")

    return score, " ".join(reasons[:2])


@router.get("", response_model=list[ExerciseRead])
def list_exercises(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    muscle_group: str | None = Query(default=None),
):
    filters = _build_filters(current_user, name, category, equipment, muscle_group)
    query = select(Exercise).where(and_(*filters)).order_by(Exercise.name.asc())
    return list(db.scalars(query).all())


@router.get("/catalog", response_model=ExerciseCatalogResponse)
def list_exercise_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    name: str | None = Query(default=None),
    category: str | None = Query(default=None),
    equipment: str | None = Query(default=None),
    muscle_group: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
):
    filters = _build_filters(current_user, name, category, equipment, muscle_group)

    total = db.scalar(select(func.count(Exercise.id)).where(and_(*filters))) or 0
    total_pages = max(1, ceil(total / page_size)) if total else 1
    current_page = min(page, total_pages)
    offset = (current_page - 1) * page_size

    items = list(
        db.scalars(
            select(Exercise)
            .where(and_(*filters))
            .order_by(Exercise.name.asc())
            .offset(offset)
            .limit(page_size)
        ).all()
    )

    return ExerciseCatalogResponse(
        items=[_serialize_exercise(item) for item in items],
        total=total,
        page=current_page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/meta", response_model=ExerciseFilterMetaResponse)
def list_exercise_meta(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = _visibility_filter(current_user)

    categories = list(db.scalars(select(distinct(Exercise.category)).where(base).order_by(Exercise.category.asc())).all())
    equipments = list(db.scalars(select(distinct(Exercise.equipment)).where(base).order_by(Exercise.equipment.asc())).all())
    muscle_groups = list(
        db.scalars(select(distinct(Exercise.muscle_group)).where(base).order_by(Exercise.muscle_group.asc())).all()
    )

    return ExerciseFilterMetaResponse(
        categories=[str(item) for item in categories if item],
        equipments=[str(item) for item in equipments if item],
        muscle_groups=[str(item) for item in muscle_groups if item],
    )


@router.post("/suggest", response_model=ExerciseSuggestResponse)
def suggest_exercises(payload: ExerciseSuggestRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    filters = [_visibility_filter(current_user)]

    available_equipment = {item for item in (payload.available_equipment or []) if item}
    if available_equipment:
        filters.append(or_(Exercise.equipment.in_(available_equipment), Exercise.equipment == "Bodyweight"))

    candidates = list(db.scalars(select(Exercise).where(and_(*filters))).all())

    scored: list[tuple[Exercise, int, str]] = []
    for exercise in candidates:
        score, reason = _score_and_reason(exercise, payload.goal, payload.session_focus, available_equipment or None)
        if score > 0:
            scored.append((exercise, score, reason))

    scored.sort(key=lambda item: (-item[1], item[0].name))

    selected: list[tuple[Exercise, str]] = []
    category_counts: dict[str, int] = {}
    muscle_counts: dict[str, int] = {}

    for exercise, _score, reason in scored:
        if len(selected) >= payload.limit:
            break

        if category_counts.get(exercise.category, 0) >= 3:
            continue
        if muscle_counts.get(exercise.muscle_group, 0) >= 2:
            continue

        selected.append((exercise, reason))
        category_counts[exercise.category] = category_counts.get(exercise.category, 0) + 1
        muscle_counts[exercise.muscle_group] = muscle_counts.get(exercise.muscle_group, 0) + 1

    if len(selected) < payload.limit:
        selected_ids = {item[0].id for item in selected}
        for exercise, _score, reason in scored:
            if len(selected) >= payload.limit:
                break
            if exercise.id in selected_ids:
                continue
            selected.append((exercise, reason))
            selected_ids.add(exercise.id)

    suggestions = []
    for exercise, reason in selected:
        sets, reps, target_rpe, rest_seconds = _prescription_for_goal(payload.goal, exercise.category)
        suggestions.append(
            ExerciseSuggestion(
                exercise_id=str(exercise.id),
                name=exercise.name,
                category=exercise.category,
                equipment=exercise.equipment,
                muscle_group=exercise.muscle_group,
                reason=reason,
                sets=sets,
                reps=reps,
                target_rpe=target_rpe,
                rest_seconds=rest_seconds,
            )
        )

    return ExerciseSuggestResponse(goal=payload.goal, session_focus=payload.session_focus, suggestions=suggestions)


@router.post("", response_model=ExerciseRead, status_code=status.HTTP_201_CREATED)
def create_exercise(payload: ExerciseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    created_by = None if current_user.role == "admin" else current_user.id
    exercise = Exercise(**payload.model_dump(), created_by_trainer_id=created_by)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def _get_visible_exercise(db: Session, exercise_id: UUID, user: User) -> Exercise:
    exercise = db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.created_by_trainer_id and exercise.created_by_trainer_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Not allowed")
    return exercise


@router.get("/{exercise_id}", response_model=ExerciseRead)
def get_exercise(exercise_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_visible_exercise(db, exercise_id, current_user)


@router.put("/{exercise_id}", response_model=ExerciseRead)
def update_exercise(
    exercise_id: UUID, payload: ExerciseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    exercise = _get_visible_exercise(db, exercise_id, current_user)
    if exercise.created_by_trainer_id is None and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can edit global exercises")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(exercise, key, value)
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exercise(exercise_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    exercise = _get_visible_exercise(db, exercise_id, current_user)
    if exercise.created_by_trainer_id is None and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admin can delete global exercises")
    db.delete(exercise)
    db.commit()
    return None
