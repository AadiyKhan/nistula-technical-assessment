from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Conversation, Message
from .schemas import AnalyticsOverview


class AnalyticsService:
    def __init__(self, session: Session):
        self.session = session

    def overview(self) -> AnalyticsOverview:
        total_messages = int(self.session.scalar(select(func.count()).select_from(Message)) or 0)
        inbound_messages = int(
            self.session.scalar(select(func.count()).select_from(Message).where(Message.direction == "inbound")) or 0
        )
        outbound_messages = int(
            self.session.scalar(select(func.count()).select_from(Message).where(Message.direction == "outbound")) or 0
        )
        complaints = int(self.session.scalar(select(func.count()).select_from(Message).where(Message.query_type == "complaint")) or 0)
        open_conversations = int(
            self.session.scalar(select(func.count()).select_from(Conversation).where(Conversation.is_open.is_(True))) or 0
        )
        avg_confidence = float(self.session.scalar(select(func.coalesce(func.avg(Message.ai_confidence_score), 0.0))) or 0.0)
        auto_send_rate = 0.0
        if total_messages:
            auto_sent = int(self.session.scalar(select(func.count()).select_from(Message).where(Message.auto_sent.is_(True))) or 0)
            auto_send_rate = round(auto_sent / total_messages, 2)

        by_channel_rows = self.session.execute(
            select(Message.source_channel, func.count()).group_by(Message.source_channel).order_by(Message.source_channel)
        ).all()
        by_query_rows = self.session.execute(
            select(Message.query_type, func.count()).where(Message.query_type.is_not(None)).group_by(Message.query_type)
        ).all()
        top_property_row = self.session.execute(
            select(Conversation.property_id, func.count())
            .select_from(Message)
            .join(Conversation, Message.conversation_id == Conversation.conversation_id)
            .where(Conversation.property_id.is_not(None))
            .group_by(Conversation.property_id)
            .order_by(func.count().desc())
            .limit(1)
        ).first()

        return AnalyticsOverview(
            total_messages=total_messages,
            inbound_messages=inbound_messages,
            outbound_messages=outbound_messages,
            complaints=complaints,
            auto_send_rate=auto_send_rate,
            average_confidence=round(avg_confidence, 2),
            open_conversations=open_conversations,
            by_channel={row[0]: int(row[1]) for row in by_channel_rows},
            by_query_type={row[0]: int(row[1]) for row in by_query_rows if row[0] is not None},
            top_property_id=str(top_property_row[0]) if top_property_row else None,
            top_property_count=int(top_property_row[1]) if top_property_row else 0,
        )