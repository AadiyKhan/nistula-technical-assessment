from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import get_db
from ..schemas import IntegrationWebhookResponse
from ..services.message_service import MessageService
from ..integrations.factory import get_channel_adapter


router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/channels")
def supported_channels() -> dict[str, list[str]]:
    return {"channels": ["whatsapp", "booking_com", "airbnb", "email"]}


@router.post("/{channel}/webhook", response_model=IntegrationWebhookResponse)
def receive_channel_message(channel: str, payload: dict[str, Any], session: Session = Depends(get_db)) -> IntegrationWebhookResponse:
    try:
        adapter = get_channel_adapter(channel)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    normalized = adapter.normalize(payload)
    settings = get_settings()
    processing_result = MessageService(session, settings).process(normalized.to_inbound_request())

    return IntegrationWebhookResponse(
        channel=channel,
        external_message_id=normalized.external_message_id,
        normalized_message_id=processing_result.response.message_id,
        message_id=processing_result.inbound_message.message_id,
        query_type=processing_result.response.query_type,
        drafted_reply=processing_result.response.drafted_reply,
        confidence_score=processing_result.response.confidence_score,
        action=processing_result.response.action,
    )
