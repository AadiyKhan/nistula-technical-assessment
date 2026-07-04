from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from .config import get_settings


def apply_migrations() -> None:
    settings = get_settings()
    if not settings.run_migrations_on_startup:
        return

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")
