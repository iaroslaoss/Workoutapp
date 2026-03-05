from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import ORMModel


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    notes: str | None = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    notes: str | None = None


class ClientRead(ORMModel):
    id: str
    trainer_id: str
    name: str
    email: str | None
    notes: str | None
