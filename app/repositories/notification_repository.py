from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ..models import NotificationEventRecord


class NotificationRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_event(self, event_type: str, payload: dict) -> NotificationEventRecord:
        record = NotificationEventRecord(event_type=event_type, payload=payload)
        self.session.add(record)
        self.session.flush()
        return record

    def list_recent_events(self, limit: int = 50) -> list[NotificationEventRecord]:
        stmt = select(NotificationEventRecord).order_by(desc(NotificationEventRecord.created_at)).limit(limit)
        return list(self.session.scalars(stmt).all())
