from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import os


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    gemini_model: str
    database_url: str
    redis_url: str | None
    celery_broker_url: str | None
    celery_result_backend: str | None
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_minutes: int
    run_migrations_on_startup: bool
    environment: str
    auto_send_threshold: float = 0.85
    agent_review_threshold: float = 0.60

    @property
    def anthropic_api_key(self) -> str | None:
        return self.gemini_api_key

    @property
    def anthropic_model(self) -> str:
        return self.gemini_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("ANTHROPIC_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL") or os.getenv("ANTHROPIC_MODEL", "gemini-3-flash"),
        database_url=os.getenv("DATABASE_URL", "sqlite:///./nistula.db"),
        redis_url=os.getenv("REDIS_URL"),
        celery_broker_url=os.getenv("CELERY_BROKER_URL") or os.getenv("REDIS_URL"),
        celery_result_backend=os.getenv("CELERY_RESULT_BACKEND") or os.getenv("REDIS_URL"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-only-secret-change-me-use-32-chars"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "480")),
        run_migrations_on_startup=os.getenv("RUN_MIGRATIONS_ON_STARTUP", "true").lower() in {"1", "true", "yes", "on"},
        environment=os.getenv("APP_ENV", "development"),
    )
