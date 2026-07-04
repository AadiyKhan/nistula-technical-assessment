from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..schemas import SourceChannel
from .base import ChannelMessage


class EmailAdapter:
    source = SourceChannel.direct

    def normalize(self, payload: dict[str, Any]) -> ChannelMessage:
        guest_name = str(payload.get("guest_name") or payload.get("from_name") or payload.get("name") or _name_from_email(payload.get("from_email")) or "Guest")
        subject = str(payload.get("subject") or "Guest email")
        body = str(payload.get("body") or payload.get("message") or "")
        message = f"{subject}\n\n{body}".strip()
        timestamp = _parse_timestamp(payload.get("timestamp"))
        return ChannelMessage(
            source=self.source,
            guest_name=guest_name,
            message=message,
            timestamp=timestamp,
            booking_ref=_optional_str(payload.get("booking_ref") or payload.get("reservationCode")),
            property_id=_optional_str(payload.get("property_id") or payload.get("propertyCode")),
            external_message_id=_optional_str(payload.get("message_id") or payload.get("id")),
        )


def _name_from_email(value: Any) -> str | None:
    if not value:
        return None
    email_text = str(value).strip()
    if "@" not in email_text:
        return None
    return email_text.split("@", 1)[0].replace(".", " ").replace("_", " ").title()


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
