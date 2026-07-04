from __future__ import annotations

from .airbnb import AirbnbAdapter
from .booking import BookingComAdapter
from .email import EmailAdapter
from .whatsapp import WhatsAppAdapter


def get_channel_adapter(channel: str):
    normalized = channel.lower().strip()
    adapters = {
        "whatsapp": WhatsAppAdapter(),
        "booking_com": BookingComAdapter(),
        "airbnb": AirbnbAdapter(),
        "email": EmailAdapter(),
    }
    if normalized not in adapters:
        raise ValueError(f"Unsupported channel: {channel}")
    return adapters[normalized]
