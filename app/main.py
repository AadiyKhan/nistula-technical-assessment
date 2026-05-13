from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .classification import classify_message, confidence_for_query_type, decide_action
from .claude_client import ClaudeDraftClient
from .config import get_settings
from .schemas import InboundMessageRequest, NormalizedMessage, WebhookResponse

app = FastAPI(title="Nistula Guest Message Handler", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/webhook/message", response_model=WebhookResponse)
def receive_message(payload: InboundMessageRequest) -> WebhookResponse:
    settings = get_settings()
    query_type = classify_message(payload.message)
    normalized = NormalizedMessage(
        source=payload.source,
        guest_name=payload.guest_name,
        message_text=payload.message,
        timestamp=payload.timestamp,
        booking_ref=payload.booking_ref,
        property_id=payload.property_id,
        query_type=query_type,
    )

    if query_type == "complaint" and not settings.anthropic_api_key:
        drafted_reply = (
            f"Hi {payload.guest_name.split()[0]} — I’m sorry for the trouble. "
            "I’m escalating this to our on-call team now and a human will follow up shortly."
        )
        confidence = 0.48
        action = "escalate"
        return WebhookResponse(
            message_id=normalized.message_id,
            query_type=query_type,
            drafted_reply=drafted_reply,
            confidence_score=confidence,
            action=action,
        )

    client = ClaudeDraftClient(settings.anthropic_api_key, settings.anthropic_model)
    draft_result = client.draft_reply(normalized)
    confidence = confidence_for_query_type(
        query_type=query_type,
        message_text=payload.message,
        drafted_reply=draft_result.drafted_reply,
        used_claude=draft_result.used_claude,
    )
    action = decide_action(query_type, confidence)

    if not draft_result.drafted_reply:
        raise HTTPException(status_code=502, detail="Unable to draft a reply")

    return WebhookResponse(
        message_id=normalized.message_id,
        query_type=query_type,
        drafted_reply=draft_result.drafted_reply,
        confidence_score=confidence,
        action=action,
    )
