from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_current_user
from app.db.session import get_db
from app.models.assigned_plan import AssignedPlan
from app.models.client import Client
from app.models.exercise import Exercise
from app.models.plan import PlanDay, PlanExercise, PlanTemplate
from app.models.user import User
from app.schemas.plan import (
    AssignedPlanCreate,
    AssignedPlanRead,
    ClientPlanDayView,
    ClientPlanExerciseView,
    ClientPlanView,
)

router = APIRouter(tags=["assignments"])


@router.post("/assignments", response_model=AssignedPlanRead, status_code=status.HTTP_201_CREATED)
def assign_plan(payload: AssignedPlanCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = db.scalar(select(Client).where(Client.id == payload.client_id, Client.trainer_id == current_user.id))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    plan = db.scalar(select(PlanTemplate).where(PlanTemplate.id == payload.plan_template_id, PlanTemplate.trainer_id == current_user.id))
    if not plan:
        raise HTTPException(status_code=404, detail="Plan template not found")

    existing = db.scalar(select(AssignedPlan).where(AssignedPlan.client_id == client.id))
    if existing:
        for key, value in payload.model_dump().items():
            setattr(existing, key, value)
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    assignment = AssignedPlan(**payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/client-view/{client_id}", response_model=ClientPlanView)
def client_view(client_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = db.scalar(select(Client).where(Client.id == client_id, Client.trainer_id == current_user.id))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    assignment = db.scalar(select(AssignedPlan).where(AssignedPlan.client_id == client.id, AssignedPlan.active == True))  # noqa: E712
    if not assignment:
        raise HTTPException(status_code=404, detail="No active assignment")

    plan = db.scalar(select(PlanTemplate).where(PlanTemplate.id == assignment.plan_template_id))
    days = db.scalars(
        select(PlanDay).where(PlanDay.plan_template_id == plan.id).order_by(PlanDay.week_number.asc(), PlanDay.day_name.asc())
    ).all()

    day_views: list[ClientPlanDayView] = []
    for day in days:
        entries = db.scalars(select(PlanExercise).where(PlanExercise.plan_day_id == day.id)).all()
        ex_map = {
            ex.id: ex.name
            for ex in db.scalars(select(Exercise).where(Exercise.id.in_([entry.exercise_id for entry in entries]))).all()
        } if entries else {}
        day_views.append(
            ClientPlanDayView(
                id=str(day.id),
                week_number=day.week_number,
                day_name=day.day_name,
                exercises=[
                    ClientPlanExerciseView(
                        id=str(entry.id),
                        exercise_name=ex_map.get(entry.exercise_id, "Unknown exercise"),
                        sets=entry.sets,
                        reps=entry.reps,
                        rpe=entry.rpe,
                        weight=entry.weight,
                        rest_seconds=entry.rest_seconds,
                        tempo=entry.tempo
                        or db.scalar(select(Exercise.default_tempo).where(Exercise.id == entry.exercise_id))
                        or "3-1-1-0",
                        notes=entry.notes,
                    )
                    for entry in entries
                ],
            )
        )

    return ClientPlanView(
        client_id=str(client.id),
        plan_template_id=str(plan.id),
        plan_name=plan.name,
        start_date=assignment.start_date,
        active=assignment.active,
        days=day_views,
    )
