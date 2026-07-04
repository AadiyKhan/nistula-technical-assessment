from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from ..models import Conversation, Property
from ..repositories.message_repository import MessageRepository
from ..schemas import DashboardSummary


class DashboardService:
    def __init__(self, session: Session):
        self.session = session
        self.messages = MessageRepository(session)

    def summary(self) -> DashboardSummary:
        total_properties = int(self.session.scalar(select(func.count()).select_from(Property)) or 0)
        active_conversations = int(
            self.session.scalar(select(func.count()).select_from(Conversation).where(Conversation.is_open.is_(True))) or 0
        )
        return DashboardSummary(
            total_properties=total_properties,
            active_conversations=active_conversations,
            messages_today=self.messages.count_messages_today(),
            complaints_today=self.messages.count_complaints_today(),
            auto_send_rate=self.messages.auto_send_rate_today(),
            agent_review_count=self.messages.count_agent_review_today(),
        )
