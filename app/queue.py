from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .models import NotificationEventRecord
from .repositories.notification_repository import NotificationRepository
from .realtime import notification_hub
from .tasks import process_notification_event


def dispatch_notification_event(session: Session, event_type: str, payload: dict[str, Any]) -> NotificationEventRecord:
    repository = NotificationRepository(session)
    record = repository.create_event(event_type=event_type, payload=payload)
    session.commit()

    notification_hub.publish(payload)

    try:
        if hasattr(process_notification_event, "delay"):
            process_notification_event.delay(payload)
        else:
            process_notification_event(payload)
    except Exception:
        # Local delivery already happened; Celery fan-out is best-effort.
        pass

    return record
