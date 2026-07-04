from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from .config import get_settings


PBKDF2_ITERATIONS = 390000


def hash_password(password: str, salt: str | None = None) -> str:
    salt_value = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_value), PBKDF2_ITERATIONS)
    encoded_digest = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt_value}${encoded_digest}"


def verify_password(password: str, encoded_password: str) -> bool:
    try:
        algorithm, iterations, salt, digest = encoded_password.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        expected = hash_password(password, salt=salt)
        return hmac.compare_digest(expected, encoded_password)
    except ValueError:
        return False


def create_access_token(*, subject: str, role: str, full_name: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "name": full_name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str]:
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    return payload