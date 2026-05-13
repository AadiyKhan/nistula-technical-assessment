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
