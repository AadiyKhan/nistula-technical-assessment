from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from .schemas import NormalizedMessage


PROPERTY_CONTEXT = """Property: Villa B1, Assagao, North Goa
Bedrooms: 3 | Max guests: 6 | Private pool: Yes
Check-in: 2pm | Check-out: 11am
Base rate: INR 18,000 per night (up to 4 guests)
Extra guest: INR 2,000 per night per person
WiFi password: Nistula@2024
Caretaker: Available 8am to 10pm
Chef on call: Yes, pre-booking required
Availability April 20-24: Available
Cancellation: Free up to 7 days before check-in"""


@dataclass
class ClaudeDraftResult:
    drafted_reply: str
    used_claude: bool


class ClaudeDraftClient:
    def __init__(self, api_key: str | None, model: str):
        self.api_key = api_key
        self.model = model

    def draft_reply(self, normalized_message: NormalizedMessage) -> ClaudeDraftResult:
        if not self.api_key:
            return ClaudeDraftResult(
                drafted_reply=self._fallback_reply(normalized_message),
                used_claude=False,
            )

        prompt = self._build_prompt(normalized_message)
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": 300,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        }

        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
            text = self._extract_text(data)
            return ClaudeDraftResult(drafted_reply=text or self._fallback_reply(normalized_message), used_claude=bool(text))
        except Exception:
            return ClaudeDraftResult(
                drafted_reply=self._fallback_reply(normalized_message),
                used_claude=False,
            )

    def _build_prompt(self, normalized_message: NormalizedMessage) -> str:
        return (
            "You are a hospitality support assistant for Nistula. "
            "Write a concise, warm, guest-facing reply based only on the property facts below. "
            "If the message is a complaint, acknowledge, apologize, and state that a human will follow up. "
            "Do not mention internal systems or policy.\n\n"
            f"{PROPERTY_CONTEXT}\n\n"
            f"Guest name: {normalized_message.guest_name}\n"
            f"Source: {normalized_message.source.value}\n"
            f"Query type: {normalized_message.query_type}\n"
            f"Message: {normalized_message.message_text}\n\n"
            "Return only the drafted reply text."
        )

    def _extract_text(self, data: dict) -> str:
        content = data.get("content", [])
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        return "".join(parts).strip()

    def _fallback_reply(self, normalized_message: NormalizedMessage) -> str:
        query_type = normalized_message.query_type
        name = normalized_message.guest_name.split()[0] if normalized_message.guest_name else "there"

        if query_type == "pre_sales_availability":
            return (
                f"Hi {name}! Yes — Villa B1 is available from April 20 to 24. "
                "Please share your preferred booking details and I can help with next steps."
            )
        if query_type == "pre_sales_pricing":
            return (
                f"Hi {name}! For 2 adults, the stay would be INR 18,000 per night. "
                "If your total guest count goes above 4, an additional INR 2,000 per extra guest per night applies."
            )
        if query_type == "post_sales_checkin":
            return (
                f"Hi {name}! Check-in at Villa B1 is from 2:00 pm and check-out is by 11:00 am. "
                "The WiFi password is Nistula@2024."
            )
        if query_type == "special_request":
            return (
                f"Hi {name}! Thanks for the request. Please share the details and we will check what can be arranged for you."
            )
        if query_type == "complaint":
            return (
                f"Hi {name}, I'm sorry for the inconvenience. A team member will review this immediately and come back to you as soon as possible."
            )
        return (
            f"Hi {name}! Thanks for reaching out. Please share a little more detail so I can help accurately."
        )
