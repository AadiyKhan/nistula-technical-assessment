from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..schemas import InboundMessageRequest, SourceChannel


@dataclass(frozen=True)
class ChannelMessage:
    source: SourceChannel
    guest_name: str
    message: str
    timestamp: datetime
    booking_ref: str | None = None
    property_id: str | None = None
    external_message_id: str | None = None

    def to_inbound_request(self) -> InboundMessageRequest:
        return InboundMessageRequest(
            source=self.source,
            guest_name=self.guest_name,
            message=self.message,
            timestamp=self.timestamp,
            booking_ref=self.booking_ref,
            property_id=self.property_id,
        )
