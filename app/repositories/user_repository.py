from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        return self.session.scalar(select(User).where(User.username == username))

    def get_by_id(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def list_users(self) -> list[User]:
        return list(self.session.scalars(select(User).order_by(User.username)).all())

    def create_user(self, *, username: str, full_name: str, password_hash: str, role: str) -> User:
        user = User(username=username, full_name=full_name, password_hash=password_hash, role=role)
        self.session.add(user)
        self.session.flush()
        return user