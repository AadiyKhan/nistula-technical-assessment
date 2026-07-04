from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from google import genai
from google.genai import types

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
class GeminiDraftResult:
    drafted_reply: str
    used_gemini: bool


class GeminiDraftClient:
    def __init__(self, api_key: str | None, model: str | None):
        self.api_key = api_key
        self.model = model or "gemini-3-flash"

    def draft_reply(
        self,
        normalized_message: NormalizedMessage,
        property_context: str | None = None,
        conversation_history: Sequence[str] | None = None,
    ) -> GeminiDraftResult:
        if not self.api_key:
            return GeminiDraftResult(
                drafted_reply=self._fallback_reply(normalized_message),
                used_gemini=False,
            )

        prompt = self._build_prompt(normalized_message, property_context, conversation_history)

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=300,
                ),
            )
            text = (getattr(response, "text", "") or "").strip()
            return GeminiDraftResult(
                drafted_reply=text or self._fallback_reply(normalized_message),
                used_gemini=bool(text),
            )
        except Exception:
            return GeminiDraftResult(
                drafted_reply=self._fallback_reply(normalized_message),
                used_gemini=False,
            )

    def _build_prompt(
        self,
        normalized_message: NormalizedMessage,
        property_context: str | None = None,
        conversation_history: Sequence[str] | None = None,
    ) -> str:
        property_block = property_context or PROPERTY_CONTEXT
        history_block = "\n".join(conversation_history or [])
        return (
            "You are a hospitality support assistant for Nistula. "
            "Write a concise, warm, guest-facing reply based only on the property facts below. "
            "If the message is a complaint, acknowledge, apologize, and state that a human will follow up. "
            "Do not mention internal systems or policy.\n\n"
            f"{property_block}\n\n"
            f"Conversation history (most recent last):\n{history_block or 'None'}\n\n"
            f"Guest name: {normalized_message.guest_name}\n"
            f"Source: {normalized_message.source.value}\n"
            f"Query type: {normalized_message.query_type}\n"
            f"Message: {normalized_message.message_text}\n\n"
            "Return only the drafted reply text."
        )

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