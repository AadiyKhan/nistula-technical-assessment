from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .db import get_db
from .repositories.user_repository import UserRepository
from .schemas import UserSummary
from .security import create_access_token, decode_access_token, verify_password


bearer_scheme = HTTPBearer(auto_error=False)


def authenticate_user(session: Session, username: str, password: str):
    user = UserRepository(session).get_by_username(username)
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return user


def issue_token(session: Session, username: str, password: str):
    user = authenticate_user(session, username, password)
    token = create_access_token(subject=user.user_id, role=user.role, full_name=user.full_name)
    return token, user


def get_user_from_token(session: Session, token: str):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    payload = decode_access_token(token)
    user = UserRepository(session).get_by_id(payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return get_user_from_token(session, credentials.credentials)


def require_roles(*allowed_roles: str) -> Callable:
    def dependency(current_user=Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


def to_user_summary(user) -> UserSummary:
    return UserSummary(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
    )