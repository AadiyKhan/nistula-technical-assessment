from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class Property(Base, TimestampMixin):
    __tablename__ = "properties"

    property_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    city: Mapped[str | None] = mapped_column(String(120))
    base_rate: Mapped[str | None] = mapped_column(String(80))
    max_guests: Mapped[int | None] = mapped_column(Integer)
    availability: Mapped[str | None] = mapped_column(String(120))
    context_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Guest(Base, TimestampMixin):
    __tablename__ = "guests"

    guest_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    phone: Mapped[str | None] = mapped_column(String(50), unique=True)

    conversations: Mapped[list["Conversation"]] = relationship(back_populates="guest")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(40), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Reservation(Base, TimestampMixin):
    __tablename__ = "reservations"

    reservation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    booking_ref: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    property_id: Mapped[str] = mapped_column(ForeignKey("properties.property_id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.guest_id"), nullable=False)
    check_in_date: Mapped[datetime | None] = mapped_column(Date)
    check_out_date: Mapped[datetime | None] = mapped_column(Date)
    reservation_status: Mapped[str] = mapped_column(String(40), default="confirmed", nullable=False)


class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"

    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.guest_id"), nullable=False)
    reservation_id: Mapped[str | None] = mapped_column(ForeignKey("reservations.reservation_id"))
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    property_id: Mapped[str | None] = mapped_column(ForeignKey("properties.property_id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    guest: Mapped[Guest] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")


class Message(Base, TimestampMixin):
    __tablename__ = "messages"

    message_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.conversation_id"), nullable=False)
    guest_id: Mapped[str] = mapped_column(ForeignKey("guests.guest_id"), nullable=False)
    reservation_id: Mapped[str | None] = mapped_column(ForeignKey("reservations.reservation_id"))
    source_channel: Mapped[str] = mapped_column(String(40), nullable=False)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(120))
    parent_message_id: Mapped[str | None] = mapped_column(ForeignKey("messages.message_id"))
    message_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text)
    raw_payload: Mapped[dict | None] = mapped_column(JSON)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    query_type: Mapped[str | None] = mapped_column(String(80))
    ai_confidence_score: Mapped[float | None] = mapped_column(Float)
    ai_model: Mapped[str | None] = mapped_column(String(120))
    ai_drafted_reply: Mapped[str | None] = mapped_column(Text)
    final_reply_text: Mapped[str | None] = mapped_column(Text)
    workflow_state: Mapped[str] = mapped_column(String(40), default="received", nullable=False)
    drafted_by_ai: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_by_agent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_by_agent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auto_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation: Mapped[Conversation] = relationship(back_populates="messages")


class MessageEvent(Base):
    __tablename__ = "message_events"

    message_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    message_id: Mapped[str] = mapped_column(ForeignKey("messages.message_id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    event_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class NotificationEventRecord(Base):
    __tablename__ = "notification_events"

    notification_event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
