from datetime import datetime

from pydantic import EmailStr

from app.schemas.common import ORMModel


class UserRead(ORMModel):
    id: str
    email: EmailStr
    role: str
    created_at: datetime
