from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select, func
from sqlalchemy.orm import Session

from ..models import Message, MessageEvent


class MessageRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_message(self, **kwargs) -> Message:
        message = Message(**kwargs)
        self.session.add(message)
        self.session.flush()
        return message

    def add_event(self, message_id: str, event_type: str, event_data: dict | None = None) -> MessageEvent:
        event = MessageEvent(message_id=message_id, event_type=event_type, event_data=event_data)
        self.session.add(event)
        self.session.flush()
        return event

    def list_recent_messages(self, conversation_id: str, limit: int = 50) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(desc(Message.received_at)).limit(limit)
        return list(self.session.scalars(stmt).all())

    def list_latest_messages(self, limit: int = 8) -> list[Message]:
        stmt = select(Message).order_by(desc(Message.received_at)).limit(limit)
        return list(self.session.scalars(stmt).all())

    def count_messages_today(self) -> int:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(self.session.scalar(select(func.count()).select_from(Message).where(Message.received_at >= start)) or 0)

    def count_complaints_today(self) -> int:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.received_at >= start)
                .where(Message.query_type == "complaint")
            )
            or 0
        )

    def count_agent_review_today(self) -> int:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(
            self.session.scalar(
                select(func.count())
                .select_from(Message)
                .where(Message.received_at >= start)
                .where(Message.workflow_state == "agent_review")
            )
            or 0
        )

    def auto_send_rate_today(self) -> float:
        start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        total = int(self.session.scalar(select(func.count()).select_from(Message).where(Message.received_at >= start)) or 0)
        if not total:
            return 0.0
        auto_sent = int(
            self.session.scalar(
                select(func.count()).select_from(Message).where(Message.received_at >= start).where(Message.auto_sent.is_(True))
            )
            or 0
        )
        return round(auto_sent / total, 2)

    def count_by_source(self) -> dict[str, int]:
        rows = self.session.execute(select(Message.source_channel, func.count()).group_by(Message.source_channel)).all()
        return {row[0]: int(row[1]) for row in rows}

    def count_by_query_type(self) -> dict[str, int]:
        rows = self.session.execute(
            select(Message.query_type, func.count()).where(Message.query_type.is_not(None)).group_by(Message.query_type)
        ).all()
        return {row[0]: int(row[1]) for row in rows if row[0] is not None}
