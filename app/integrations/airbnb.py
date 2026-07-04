from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..schemas import SourceChannel
from .base import ChannelMessage


class AirbnbAdapter:
    source = SourceChannel.airbnb

    def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        guest_name = str(payload.get("guest_name") or payload.get("guestName") or payload.get("name") or "Guest")
        message = str(payload.get("message") or payload.get("thread_message") or payload.get("body") or "")
        timestamp = _parse_timestamp(payload.get("timestamp"))
        return ChannelMessage(
            source=self.source,
            guest_name=guest_name,
            message=message,
            timestamp=timestamp,
            booking_ref=_optional_str(payload.get("booking_ref") or payload.get("reservationCode") or payload.get("reservation_id")),
            property_id=_optional_str(payload.get("property_id") or payload.get("propertyCode")),
            external_message_id=_optional_str(payload.get("message_id") or payload.get("id")),
        )


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_timestamp(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)
