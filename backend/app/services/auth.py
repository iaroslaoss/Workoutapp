from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User


def register_trainer(db: Session, email: str, password: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing:
        raise ValueError("Email already in use")

    user = User(email=email, password_hash=get_password_hash(password), role="trainer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login(db: Session, email: str, password: str) -> str | None:
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(password, user.password_hash):
        return None
    return create_access_token(str(user.id))
