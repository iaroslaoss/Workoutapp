from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.deps import get_current_user
from app.db.session import get_db
from app.models.assigned_plan import AssignedPlan
from app.models.client import Client
from app.models.plan import PlanTemplate
from app.models.user import User
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate
from app.schemas.plan import AssignmentSummary, AssignedPlanRead, PlanTemplateRead

router = APIRouter(prefix="/clients", tags=["clients"])


@router.get("", response_model=list[ClientRead])
def list_clients(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return list(db.scalars(select(Client).where(Client.trainer_id == current_user.id).order_by(Client.name.asc())).all())


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = Client(trainer_id=current_user.id, **payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def _trainer_client_or_404(db: Session, client_id: UUID, user: User) -> Client:
    client = db.scalar(select(Client).where(Client.id == client_id, Client.trainer_id == user.id))
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _trainer_client_or_404(db, client_id, current_user)


@router.put("/{client_id}", response_model=ClientRead)
def update_client(client_id: UUID, payload: ClientUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = _trainer_client_or_404(db, client_id, current_user)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    client = _trainer_client_or_404(db, client_id, current_user)
    db.delete(client)
    db.commit()
    return None


@router.get("/{client_id}/assignment", response_model=AssignmentSummary)
def get_assignment(client_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _trainer_client_or_404(db, client_id, current_user)
    assignment = db.scalar(select(AssignedPlan).where(AssignedPlan.client_id == client_id))
    if not assignment:
        return AssignmentSummary(assignment=None, plan=None)

    plan = db.scalar(select(PlanTemplate).where(PlanTemplate.id == assignment.plan_template_id))
    return AssignmentSummary(assignment=AssignedPlanRead.model_validate(assignment), plan=PlanTemplateRead.model_validate(plan))
