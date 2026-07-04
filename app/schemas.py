from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class SourceChannel(str, Enum):
    whatsapp = "whatsapp"
    booking_com = "booking_com"
    airbnb = "airbnb"
    instagram = "instagram"
    direct = "direct"


class IntegrationChannel(str, Enum):
    whatsapp = "whatsapp"
    booking_com = "booking_com"
    airbnb = "airbnb"
    email = "email"


QueryType = Literal[
    "pre_sales_availability",
    "pre_sales_pricing",
    "post_sales_checkin",
    "special_request",
    "complaint",
    "general_enquiry",
]


class InboundMessageRequest(BaseModel):
    source: SourceChannel
    guest_name: str = Field(min_length=1)
    message: str = Field(min_length=1)
    timestamp: datetime
    booking_ref: str | None = None
    property_id: str | None = None

    @field_validator("guest_name", "message", "booking_ref", "property_id", mode="before")
    @classmethod
    def empty_string_to_none_or_strip(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class NormalizedMessage(BaseModel):
    message_id: UUID = Field(default_factory=uuid4)
    source: SourceChannel
    guest_name: str
    message_text: str
    timestamp: datetime
    booking_ref: str | None = None
    property_id: str | None = None
    query_type: QueryType


class WebhookResponse(BaseModel):
    message_id: UUID
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: Literal["auto_send", "agent_review", "escalate"]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class UserSummary(BaseModel):
    user_id: UUID
    username: str
    full_name: str
    role: Literal["owner", "manager", "support", "housekeeping"]
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserSummary


class PropertySummary(BaseModel):
    property_id: str
    name: str
    city: str | None = None
    base_rate: str | None = None
    max_guests: int | None = None
    availability: str | None = None
    context: str


class DashboardSummary(BaseModel):
    total_properties: int
    active_conversations: int
    messages_today: int
    complaints_today: int
    auto_send_rate: float
    agent_review_count: int


class ConversationMessage(BaseModel):
    message_id: UUID
    direction: Literal["inbound", "outbound"]
    message_text: str
    query_type: QueryType | None = None
    ai_confidence_score: float | None = None
    workflow_state: str
    received_at: datetime


class AnalyticsOverview(BaseModel):
    total_messages: int
    inbound_messages: int
    outbound_messages: int
    complaints: int
    auto_send_rate: float
    average_confidence: float
    open_conversations: int
    by_channel: dict[str, int]
    by_query_type: dict[str, int]
    top_property_id: str | None = None
    top_property_count: int = 0


class NotificationEvent(BaseModel):
    event_type: str
    message_id: UUID
    conversation_id: UUID
    property_id: str | None = None
    query_type: QueryType | None = None
    action: str
    confidence_score: float
    drafted_reply: str
    created_at: datetime


class IntegrationWebhookRequest(BaseModel):
    channel: IntegrationChannel
    payload: dict[str, object]


class IntegrationWebhookResponse(BaseModel):
    channel: IntegrationChannel
    external_message_id: str | None = None
    normalized_message_id: UUID
    message_id: UUID
    query_type: QueryType
    drafted_reply: str
    confidence_score: float
    action: Literal["auto_send", "agent_review", "escalate"]
