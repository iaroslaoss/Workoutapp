from copy import deepcopy
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.db.deps import get_current_user
from app.db.session import get_db
from app.models.exercise import Exercise
from app.models.plan import PlanDay, PlanExercise, PlanTemplate
from app.models.user import User
from app.schemas.plan import (
    DuplicateDayRequest,
    DuplicatePlanRequest,
    PlanDayCreate,
    PlanDayRead,
    PlanDayUpdate,
    PlanExerciseCreate,
    PlanExerciseRead,
    PlanExerciseUpdate,
    PlanTemplateCreate,
    PlanTemplateRead,
    PlanTemplateUpdate,
    StarterPlanImportResponse,
    StarterPlanSuggestionRead,
)

router = APIRouter(tags=["plans"])

STARTER_PLAN_LIBRARY: dict[str, dict] = {
    "beginner-full-body-3-day": {
        "name": "Beginner Full Body 3-Day",
        "description": "Simple full-body progression for new lifters. Balanced strength, skill, and consistency.",
        "weeks_count": 8,
        "goal": "general_fitness",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Barbell Back Squat", 4, "6-8", 7, 120),
                    ("Barbell Bench Press", 4, "6-8", 7, 120),
                    ("Seated Cable Row", 3, "8-10", 7, 90),
                    ("Plank", 3, "30-45 sec", 6, 45),
                ],
            },
            {
                "day_name": "Wed",
                "items": [
                    ("Romanian Deadlift", 4, "6-8", 7, 120),
                    ("Overhead Press", 3, "6-8", 7, 90),
                    ("Walking Lunge", 3, "10-12", 7, 75),
                    ("Dead Bug", 3, "8-10", 6, 45),
                ],
            },
            {
                "day_name": "Fri",
                "items": [
                    ("Leg Press", 3, "10-12", 7, 90),
                    ("Incline Dumbbell Press", 3, "8-10", 7, 90),
                    ("Pull-Up", 3, "4-8", 8, 90),
                    ("Farmer Carry", 3, "30-40 m", 7, 60),
                ],
            },
        ],
    },
    "beginner-upper-lower-4-day": {
        "name": "Beginner Upper/Lower 4-Day",
        "description": "Classic upper-lower split for building strength while managing fatigue.",
        "weeks_count": 8,
        "goal": "strength",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Barbell Bench Press", 4, "5-7", 8, 150),
                    ("Seated Cable Row", 4, "6-8", 8, 120),
                    ("Overhead Press", 3, "6-8", 7, 120),
                    ("Face Pull", 3, "12-15", 7, 60),
                ],
            },
            {
                "day_name": "Tue",
                "items": [
                    ("Barbell Back Squat", 4, "5-7", 8, 150),
                    ("Romanian Deadlift", 3, "6-8", 8, 120),
                    ("Walking Lunge", 3, "10-12", 7, 75),
                    ("Plank", 3, "30-45 sec", 6, 45),
                ],
            },
            {
                "day_name": "Thu",
                "items": [
                    ("Incline Dumbbell Press", 4, "6-8", 8, 120),
                    ("Pull-Up", 3, "4-8", 8, 120),
                    ("Seated Cable Row", 3, "8-10", 7, 90),
                    ("Dead Bug", 3, "8-10", 6, 45),
                ],
            },
            {
                "day_name": "Sat",
                "items": [
                    ("Leg Press", 4, "8-10", 8, 120),
                    ("Hamstring Curl", 3, "10-12", 7, 75),
                    ("Farmer Carry", 3, "30-40 m", 7, 60),
                    ("Air Bike Intervals", 4, "30-40 sec", 7, 45),
                ],
            },
        ],
    },
    "beginner-push-pull-legs": {
        "name": "Beginner Push Pull Legs",
        "description": "Simple push-pull-legs structure with moderate volume and technique focus.",
        "weeks_count": 6,
        "goal": "hypertrophy",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Barbell Bench Press", 4, "6-10", 8, 120),
                    ("Overhead Press", 3, "8-10", 7, 90),
                    ("Incline Dumbbell Press", 3, "8-12", 7, 75),
                    ("Plank", 3, "30-45 sec", 6, 45),
                ],
            },
            {
                "day_name": "Wed",
                "items": [
                    ("Pull-Up", 3, "4-8", 8, 120),
                    ("Seated Cable Row", 4, "8-12", 7, 90),
                    ("Romanian Deadlift", 3, "8-10", 8, 120),
                    ("Face Pull", 3, "12-15", 7, 60),
                ],
            },
            {
                "day_name": "Fri",
                "items": [
                    ("Barbell Back Squat", 4, "6-10", 8, 120),
                    ("Leg Press", 3, "10-12", 7, 90),
                    ("Hamstring Curl", 3, "10-12", 7, 75),
                    ("Dead Bug", 3, "8-10", 6, 45),
                ],
            },
        ],
    },
    "beginner-home-dumbbell-3-day": {
        "name": "Beginner Home Dumbbell 3-Day",
        "description": "Home-friendly dumbbell and bodyweight plan requiring minimal setup.",
        "weeks_count": 8,
        "goal": "general_fitness",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Push-Up", 4, "8-12", 7, 60),
                    ("Single-Arm Dumbbell Row", 4, "8-12", 7, 75),
                    ("Walking Lunge", 3, "10-12", 7, 60),
                    ("Plank", 3, "30-45 sec", 6, 45),
                ],
            },
            {
                "day_name": "Wed",
                "items": [
                    ("Incline Dumbbell Press", 4, "8-12", 7, 75),
                    ("Bulgarian Split Squat", 3, "8-10", 8, 75),
                    ("Overhead Press", 3, "8-10", 7, 75),
                    ("Dead Bug", 3, "8-10", 6, 45),
                ],
            },
            {
                "day_name": "Fri",
                "items": [
                    ("Single-Arm Dumbbell Row", 4, "8-12", 7, 75),
                    ("Walking Lunge", 3, "10-12", 7, 60),
                    ("Push-Up", 3, "AMRAP", 8, 60),
                    ("Farmer Carry", 3, "25-40 m", 7, 60),
                ],
            },
        ],
    },
    "beginner-fat-loss-circuits": {
        "name": "Beginner Fat Loss Circuits",
        "description": "Low-complexity, higher-density sessions to improve conditioning and body composition.",
        "weeks_count": 6,
        "goal": "fat_loss",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Push-Up", 3, "10-15", 7, 30),
                    ("Walking Lunge", 3, "12-14", 7, 30),
                    ("Seated Cable Row", 3, "10-12", 7, 45),
                    ("Air Bike Intervals", 5, "30-40 sec", 7, 30),
                ],
            },
            {
                "day_name": "Wed",
                "items": [
                    ("Leg Press", 3, "12-15", 7, 45),
                    ("Incline Dumbbell Press", 3, "10-12", 7, 45),
                    ("Face Pull", 3, "12-15", 7, 30),
                    ("Rower Intervals", 5, "30-40 sec", 7, 30),
                ],
            },
            {
                "day_name": "Sat",
                "items": [
                    ("Barbell Back Squat", 3, "8-10", 7, 60),
                    ("Pull-Up", 3, "4-8", 8, 60),
                    ("Farmer Carry", 4, "30 m", 7, 45),
                    ("Treadmill Intervals", 5, "30-45 sec", 7, 30),
                ],
            },
        ],
    },
    "beginner-strength-foundations": {
        "name": "Beginner Strength Foundations",
        "description": "Technique-first foundation around squat, hinge, press, and row patterns.",
        "weeks_count": 8,
        "goal": "strength",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Barbell Back Squat", 5, "4-6", 8, 150),
                    ("Barbell Bench Press", 5, "4-6", 8, 150),
                    ("Plank", 3, "40-60 sec", 6, 45),
                ],
            },
            {
                "day_name": "Wed",
                "items": [
                    ("Romanian Deadlift", 5, "4-6", 8, 150),
                    ("Overhead Press", 4, "5-7", 8, 120),
                    ("Seated Cable Row", 4, "6-8", 8, 120),
                ],
            },
            {
                "day_name": "Fri",
                "items": [
                    ("Leg Press", 4, "6-8", 8, 120),
                    ("Pull-Up", 4, "4-7", 8, 120),
                    ("Farmer Carry", 3, "30-40 m", 7, 60),
                ],
            },
        ],
    },
    "beginner-core-conditioning-2-day": {
        "name": "Beginner Core + Conditioning 2-Day",
        "description": "Two-day accessory template to improve trunk strength and aerobic capacity.",
        "weeks_count": 6,
        "goal": "conditioning",
        "weekly_days": [
            {
                "day_name": "Tue",
                "items": [
                    ("Plank", 4, "30-45 sec", 6, 30),
                    ("Dead Bug", 4, "8-10", 6, 30),
                    ("Farmer Carry", 4, "25-40 m", 7, 45),
                    ("Air Bike Intervals", 6, "20-30 sec", 7, 30),
                ],
            },
            {
                "day_name": "Fri",
                "items": [
                    ("Face Pull", 3, "12-15", 7, 45),
                    ("Walking Lunge", 3, "10-12", 7, 45),
                    ("Rower Intervals", 6, "20-30 sec", 7, 30),
                    ("Treadmill Intervals", 6, "20-30 sec", 7, 30),
                ],
            },
        ],
    },
    "beginner-minimal-equipment-2-day": {
        "name": "Beginner Minimal Equipment 2-Day",
        "description": "Low-volume starter plan for clients with tight schedules and limited equipment.",
        "weeks_count": 8,
        "goal": "general_fitness",
        "weekly_days": [
            {
                "day_name": "Mon",
                "items": [
                    ("Push-Up", 3, "8-12", 7, 45),
                    ("Walking Lunge", 3, "10-12", 7, 45),
                    ("Single-Arm Dumbbell Row", 3, "10-12", 7, 60),
                    ("Plank", 3, "30-40 sec", 6, 30),
                ],
            },
            {
                "day_name": "Thu",
                "items": [
                    ("Incline Dumbbell Press", 3, "8-12", 7, 60),
                    ("Bulgarian Split Squat", 3, "8-10", 7, 60),
                    ("Overhead Press", 3, "8-10", 7, 60),
                    ("Dead Bug", 3, "8-10", 6, 30),
                ],
            },
        ],
    },
}


def _trainer_plan_or_404(db: Session, plan_id: UUID, user_id: UUID) -> PlanTemplate:
    plan = db.scalar(select(PlanTemplate).where(PlanTemplate.id == plan_id, PlanTemplate.trainer_id == user_id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan template not found")
    return plan


def _plan_day_or_404(db: Session, day_id: UUID, user_id: UUID) -> PlanDay:
    day = db.scalar(
        select(PlanDay).join(PlanTemplate, PlanDay.plan_template_id == PlanTemplate.id).where(
            PlanDay.id == day_id, PlanTemplate.trainer_id == user_id
        )
    )
    if not day:
        raise HTTPException(status_code=404, detail="Plan day not found")
    return day


def _plan_exercise_or_404(db: Session, item_id: UUID, user_id: UUID) -> PlanExercise:
    row = db.scalar(
        select(PlanExercise)
        .join(PlanDay, PlanExercise.plan_day_id == PlanDay.id)
        .join(PlanTemplate, PlanDay.plan_template_id == PlanTemplate.id)
        .where(PlanExercise.id == item_id, PlanTemplate.trainer_id == user_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Plan exercise not found")
    return row


@router.get("/plans", response_model=list[PlanTemplateRead])
def list_plans(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list(db.scalars(select(PlanTemplate).where(PlanTemplate.trainer_id == current_user.id)).all())


@router.post("/plans", response_model=PlanTemplateRead, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanTemplateCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = PlanTemplate(trainer_id=current_user.id, **payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/plans/starter-suggestions", response_model=list[StarterPlanSuggestionRead])
def list_starter_suggestions(current_user: User = Depends(get_current_user)):
    _ = current_user
    suggestions = []
    for slug, data in STARTER_PLAN_LIBRARY.items():
        suggestions.append(
            StarterPlanSuggestionRead(
                slug=slug,
                name=data["name"],
                description=data["description"],
                weeks_count=data["weeks_count"],
                sessions_per_week=len(data["weekly_days"]),
                goal=data["goal"],
            )
        )
    return suggestions


@router.post("/plans/starter/{slug}/import", response_model=StarterPlanImportResponse, status_code=status.HTTP_201_CREATED)
def import_starter_plan(slug: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    starter = STARTER_PLAN_LIBRARY.get(slug)
    if not starter:
        raise HTTPException(status_code=404, detail="Starter plan not found")

    all_names = {
        item[0].lower()
        for day in starter["weekly_days"]
        for item in day["items"]
    }

    visible_exercises = db.scalars(
        select(Exercise).where(
            and_(
                func.lower(Exercise.name).in_(all_names),
                (Exercise.created_by_trainer_id.is_(None)) | (Exercise.created_by_trainer_id == current_user.id),
            )
        )
    ).all()

    ex_by_name = {exercise.name.lower(): exercise for exercise in visible_exercises}

    imported = PlanTemplate(
        trainer_id=current_user.id,
        name=f"{starter['name']} (Starter)",
        description=starter["description"],
        weeks_count=starter["weeks_count"],
    )
    db.add(imported)
    db.flush()

    days_created = 0
    exercises_created = 0
    missing_exercises: set[str] = set()

    for week in range(1, starter["weeks_count"] + 1):
        for day in starter["weekly_days"]:
            created_day = PlanDay(plan_template_id=imported.id, week_number=week, day_name=day["day_name"])
            db.add(created_day)
            db.flush()
            days_created += 1

            for ex_name, sets, reps, rpe, rest_seconds in day["items"]:
                exercise = ex_by_name.get(ex_name.lower())
                if not exercise:
                    missing_exercises.add(ex_name)
                    continue

                db.add(
                    PlanExercise(
                        plan_day_id=created_day.id,
                        exercise_id=exercise.id,
                        sets=sets,
                        reps=reps,
                        rpe=rpe,
                        weight=None,
                        rest_seconds=rest_seconds,
                        tempo=None,
                        notes="Imported from beginner starter template",
                    )
                )
                exercises_created += 1

    db.commit()
    db.refresh(imported)

    return StarterPlanImportResponse(
        plan=PlanTemplateRead(
            id=str(imported.id),
            trainer_id=str(imported.trainer_id),
            name=imported.name,
            description=imported.description,
            weeks_count=imported.weeks_count,
        ),
        days_created=days_created,
        exercises_created=exercises_created,
        missing_exercises=sorted(missing_exercises),
    )


@router.get("/plans/{plan_id}", response_model=PlanTemplateRead)
def get_plan(plan_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _trainer_plan_or_404(db, plan_id, current_user.id)


@router.put("/plans/{plan_id}", response_model=PlanTemplateRead)
def update_plan(
    plan_id: UUID, payload: PlanTemplateUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    plan = _trainer_plan_or_404(db, plan_id, current_user.id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan(plan_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = _trainer_plan_or_404(db, plan_id, current_user.id)
    db.delete(plan)
    db.commit()
    return None


@router.post("/plans/{plan_id}/duplicate", response_model=PlanTemplateRead, status_code=status.HTTP_201_CREATED)
def duplicate_plan(
    plan_id: UUID, payload: DuplicatePlanRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    original = _trainer_plan_or_404(db, plan_id, current_user.id)
    cloned = PlanTemplate(
        trainer_id=current_user.id,
        name=payload.name or f"{original.name} (Copy)",
        description=original.description,
        weeks_count=original.weeks_count,
    )
    db.add(cloned)
    db.flush()

    days = db.scalars(select(PlanDay).where(PlanDay.plan_template_id == original.id)).all()
    day_map: dict[str, PlanDay] = {}
    for day in days:
        copy_day = PlanDay(plan_template_id=cloned.id, week_number=day.week_number, day_name=day.day_name)
        db.add(copy_day)
        db.flush()
        day_map[str(day.id)] = copy_day

    items = db.scalars(select(PlanExercise).join(PlanDay).where(PlanDay.plan_template_id == original.id)).all()
    for item in items:
        data = {k: deepcopy(v) for k, v in item.__dict__.items() if not k.startswith("_") and k not in {"id", "plan_day_id"}}
        data["plan_day_id"] = day_map[str(item.plan_day_id)].id
        db.add(PlanExercise(**data))

    db.commit()
    db.refresh(cloned)
    return cloned


@router.get("/plans/{plan_id}/days", response_model=list[PlanDayRead])
def list_days(plan_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = _trainer_plan_or_404(db, plan_id, current_user.id)
    return list(
        db.scalars(select(PlanDay).where(PlanDay.plan_template_id == plan.id).order_by(PlanDay.week_number, PlanDay.day_name)).all()
    )


@router.post("/plans/{plan_id}/days", response_model=PlanDayRead, status_code=status.HTTP_201_CREATED)
def create_day(
    plan_id: UUID, payload: PlanDayCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    plan = _trainer_plan_or_404(db, plan_id, current_user.id)
    if payload.week_number > plan.weeks_count:
        raise HTTPException(status_code=400, detail="Week number out of plan bounds")

    day = PlanDay(plan_template_id=plan.id, **payload.model_dump())
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


@router.put("/days/{day_id}", response_model=PlanDayRead)
def update_day(day_id: UUID, payload: PlanDayUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = _plan_day_or_404(db, day_id, current_user.id)
    plan = _trainer_plan_or_404(db, day.plan_template_id, current_user.id)
    data = payload.model_dump(exclude_unset=True)
    if "week_number" in data and data["week_number"] > plan.weeks_count:
        raise HTTPException(status_code=400, detail="Week number out of plan bounds")
    for key, value in data.items():
        setattr(day, key, value)
    db.add(day)
    db.commit()
    db.refresh(day)
    return day


@router.delete("/days/{day_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_day(day_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = _plan_day_or_404(db, day_id, current_user.id)
    db.delete(day)
    db.commit()
    return None


@router.post("/days/duplicate", response_model=PlanDayRead, status_code=status.HTTP_201_CREATED)
def duplicate_day(
    payload: DuplicateDayRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    source = _plan_day_or_404(db, payload.source_day_id, current_user.id)
    target = _plan_day_or_404(db, payload.target_day_id, current_user.id)
    if source.plan_template_id != target.plan_template_id:
        raise HTTPException(status_code=400, detail="Source and target day must be in same plan")

    for old in db.scalars(select(PlanExercise).where(PlanExercise.plan_day_id == target.id)).all():
        db.delete(old)
    db.flush()

    source_items = db.scalars(select(PlanExercise).where(PlanExercise.plan_day_id == source.id)).all()
    for item in source_items:
        db.add(
            PlanExercise(
                plan_day_id=target.id,
                exercise_id=item.exercise_id,
                sets=item.sets,
                reps=item.reps,
                rpe=item.rpe,
                weight=item.weight,
                rest_seconds=item.rest_seconds,
                tempo=item.tempo,
                notes=item.notes,
            )
        )
    db.commit()
    db.refresh(target)
    return target


@router.get("/days/{day_id}/exercises", response_model=list[PlanExerciseRead])
def list_day_exercises(day_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    day = _plan_day_or_404(db, day_id, current_user.id)
    return list(db.scalars(select(PlanExercise).where(PlanExercise.plan_day_id == day.id)).all())


@router.post("/days/{day_id}/exercises", response_model=PlanExerciseRead, status_code=status.HTTP_201_CREATED)
def create_plan_exercise(
    day_id: UUID, payload: PlanExerciseCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    day = _plan_day_or_404(db, day_id, current_user.id)
    row = PlanExercise(plan_day_id=day.id, **payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.put("/plan-exercises/{item_id}", response_model=PlanExerciseRead)
def update_plan_exercise(
    item_id: UUID, payload: PlanExerciseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    row = _plan_exercise_or_404(db, item_id, current_user.id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/plan-exercises/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_plan_exercise(item_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = _plan_exercise_or_404(db, item_id, current_user.id)
    db.delete(row)
    db.commit()
    return None
