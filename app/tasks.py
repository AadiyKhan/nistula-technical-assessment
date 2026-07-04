from __future__ import annotations

from typing import Any

from .config import get_settings

try:
    from celery import Celery
except Exception:  # pragma: no cover - celery is installed in the workspace, but keep import-safe.
    Celery = None  # type: ignore[assignment]


def _build_celery_app():
    settings = get_settings()
    broker_url = settings.celery_broker_url
    if not Celery or not broker_url:
        return None

    celery_app = Celery(
        "nistula",
        broker=broker_url,
        backend=settings.celery_result_backend,
        include=["app.tasks"],
    )
    celery_app.conf.task_always_eager = False
    celery_app.conf.task_serializer = "json"
    celery_app.conf.accept_content = ["json"]
    celery_app.conf.result_serializer = "json"
    return celery_app


celery_app = _build_celery_app()


if celery_app:

    @celery_app.task(name="app.tasks.process_notification_event")
    def process_notification_event(event: dict[str, Any]) -> dict[str, Any]:
        # In production this task can fan out to email, Slack, SMS, or CRM hooks.
        return event
else:

    def process_notification_event(event: dict[str, Any]) -> dict[str, Any]:
        return event
