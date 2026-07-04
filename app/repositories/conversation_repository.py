from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from ..models import Conversation, Guest, Message, Reservation


class ConversationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_or_create_guest(self, full_name: str) -> Guest:
        guest = self.session.scalar(select(Guest).where(Guest.full_name == full_name))
        if guest:
            return guest
        guest = Guest(full_name=full_name)
        self.session.add(guest)
        self.session.flush()
        return guest

    def get_or_create_reservation(self, booking_ref: str | None, property_id: str | None, guest_id: str) -> Reservation | None:
        if not booking_ref:
            return None
        reservation = self.session.scalar(select(Reservation).where(Reservation.booking_ref == booking_ref))
        if reservation:
            return reservation
        reservation = Reservation(booking_ref=booking_ref, property_id=property_id or "unknown", guest_id=guest_id)
        self.session.add(reservation)
        self.session.flush()
        return reservation

    def get_or_create_conversation(
        self,
        guest_id: str,
        channel: str,
        property_id: str | None,
        reservation_id: str | None = None,
    ) -> Conversation:
        conversation = self.session.scalar(
            select(Conversation)
            .where(Conversation.guest_id == guest_id)
            .where(Conversation.channel == channel)
            .where(Conversation.property_id == property_id)
            .where(Conversation.is_open.is_(True))
            .order_by(desc(Conversation.last_message_at))
        )
        if conversation:
            return conversation

        conversation = Conversation(
            guest_id=guest_id,
            reservation_id=reservation_id,
            channel=channel,
            property_id=property_id,
            started_at=datetime.now(timezone.utc),
            last_message_at=datetime.now(timezone.utc),
            is_open=True,
        )
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def update_last_message(self, conversation: Conversation) -> None:
        conversation.last_message_at = datetime.now(timezone.utc)

    def list_conversation_messages(self, conversation_id: str, limit: int = 50) -> list[Message]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(desc(Message.received_at)).limit(limit)
        return list(self.session.scalars(stmt).all())
