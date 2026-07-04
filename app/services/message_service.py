from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ..classification import classify_message, confidence_for_query_type, decide_action
from ..config import Settings
from ..gemini_client import GeminiDraftClient
from ..models import Message
from ..repositories.conversation_repository import ConversationRepository
from ..repositories.message_repository import MessageRepository
from ..repositories.property_repository import PropertyRepository
from ..queue import dispatch_notification_event
from ..schemas import InboundMessageRequest, NormalizedMessage, WebhookResponse


@dataclass
class MessageProcessingResult:
    response: WebhookResponse
    inbound_message: Message
    outbound_message: Message | None


class MessageService:
    def __init__(self, session: Session, settings: Settings):
        self.session = session
        self.settings = settings
        self.properties = PropertyRepository(session)
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)

    def process(self, payload: InboundMessageRequest) -> MessageProcessingResult:
        query_type = classify_message(payload.message)
        property_row = self.properties.get_property(payload.property_id)
        guest = self.conversations.get_or_create_guest(payload.guest_name)
        reservation = self.conversations.get_or_create_reservation(payload.booking_ref, property_row.property_id, guest.guest_id)
        conversation = self.conversations.get_or_create_conversation(
            guest_id=guest.guest_id,
            channel=payload.source.value,
            property_id=property_row.property_id,
            reservation_id=reservation.reservation_id if reservation else None,
        )

        normalized = NormalizedMessage(
            source=payload.source,
            guest_name=payload.guest_name,
            message_text=payload.message,
            timestamp=payload.timestamp,
            booking_ref=payload.booking_ref,
            property_id=property_row.property_id,
            query_type=query_type,
        )

        recent_messages = self.messages.list_recent_messages(conversation.conversation_id, limit=50)
        history_text = [message.message_text for message in reversed(recent_messages)]
        property_context = self.properties.build_context(property_row)
        gemini_api_key = getattr(self.settings, "gemini_api_key", None) or getattr(
            self.settings, "anthropic_api_key", None
        )
        gemini_model = getattr(self.settings, "gemini_model", None) or getattr(self.settings, "anthropic_model", None)

        if query_type == "complaint" and not gemini_api_key:
            drafted_reply = (
                f"Hi {payload.guest_name.split()[0]} — I’m sorry for the trouble. "
                "I’m escalating this to our on-call team now and a human will follow up shortly."
            )
            confidence = 0.48
            action = "escalate"
            response = WebhookResponse(
                message_id=normalized.message_id,
                query_type=query_type,
                drafted_reply=drafted_reply,
                confidence_score=confidence,
                action=action,
            )
            inbound_message = self.messages.create_message(
                conversation_id=conversation.conversation_id,
                guest_id=guest.guest_id,
                reservation_id=reservation.reservation_id if reservation else None,
                source_channel=payload.source.value,
                direction="inbound",
                message_text=payload.message,
                normalized_text=payload.message,
                raw_payload=payload.model_dump(mode="json"),
                received_at=payload.timestamp,
                query_type=query_type,
                ai_confidence_score=confidence,
                ai_model=gemini_model,
                ai_drafted_reply=drafted_reply,
                final_reply_text=drafted_reply,
                workflow_state=action,
                drafted_by_ai=False,
                edited_by_agent=False,
                auto_sent=False,
            )
            self.messages.add_event(inbound_message.message_id, "escalated", {"reason": "missing_gemini_key"})
            self.conversations.update_last_message(conversation)
            dispatch_notification_event(
                self.session,
                "message_escalated",
                {
                    "event_type": "message_escalated",
                    "message_id": str(inbound_message.message_id),
                    "conversation_id": str(conversation.conversation_id),
                    "property_id": property_row.property_id,
                    "query_type": query_type,
                    "action": action,
                    "confidence_score": confidence,
                    "drafted_reply": drafted_reply,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            return MessageProcessingResult(response=response, inbound_message=inbound_message, outbound_message=None)

        client = GeminiDraftClient(gemini_api_key, gemini_model)
        draft_result = client.draft_reply(normalized, property_context=property_context, conversation_history=history_text)
        confidence = confidence_for_query_type(
            query_type=query_type,
            message_text=payload.message,
            drafted_reply=draft_result.drafted_reply,
            used_claude=draft_result.used_gemini,
        )
        action = decide_action(query_type, confidence)

        inbound_message = self.messages.create_message(
            conversation_id=conversation.conversation_id,
            guest_id=guest.guest_id,
            reservation_id=reservation.reservation_id if reservation else None,
            source_channel=payload.source.value,
            direction="inbound",
            message_text=payload.message,
            normalized_text=payload.message,
            raw_payload=payload.model_dump(mode="json"),
            received_at=payload.timestamp,
            query_type=query_type,
            ai_confidence_score=confidence,
            ai_model=gemini_model,
            ai_drafted_reply=draft_result.drafted_reply,
            final_reply_text=draft_result.drafted_reply,
            workflow_state=action,
            drafted_by_ai=bool(draft_result.drafted_reply),
            edited_by_agent=False,
            auto_sent=action == "auto_send",
            auto_sent_at=datetime.now(timezone.utc) if action == "auto_send" else None,
        )
        self.messages.add_event(inbound_message.message_id, "ai_drafted", {"used_gemini": draft_result.used_gemini})

        outbound_message = self.messages.create_message(
            conversation_id=conversation.conversation_id,
            guest_id=guest.guest_id,
            reservation_id=reservation.reservation_id if reservation else None,
            source_channel=payload.source.value,
            direction="outbound",
            parent_message_id=inbound_message.message_id,
            message_text=draft_result.drafted_reply,
            normalized_text=draft_result.drafted_reply,
            raw_payload={"reply_to": str(inbound_message.message_id)},
            sent_at=datetime.now(timezone.utc) if action == "auto_send" else None,
            query_type=query_type,
            ai_confidence_score=confidence,
            ai_model=gemini_model,
            ai_drafted_reply=draft_result.drafted_reply,
            final_reply_text=draft_result.drafted_reply,
            workflow_state=action,
            drafted_by_ai=True,
            edited_by_agent=False,
            auto_sent=action == "auto_send",
            auto_sent_at=datetime.now(timezone.utc) if action == "auto_send" else None,
        )
        if action == "auto_send":
            self.messages.add_event(outbound_message.message_id, "auto_sent", {"confidence": confidence})
        else:
            self.messages.add_event(inbound_message.message_id, action, {"confidence": confidence})

        self.conversations.update_last_message(conversation)
        dispatch_notification_event(
            self.session,
            "message_processed",
            {
                "event_type": "message_processed",
                "message_id": str(inbound_message.message_id),
                "conversation_id": str(conversation.conversation_id),
                "property_id": property_row.property_id,
                "query_type": query_type,
                "action": action,
                "confidence_score": confidence,
                "drafted_reply": draft_result.drafted_reply,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        response = WebhookResponse(
            message_id=normalized.message_id,
            query_type=query_type,
            drafted_reply=draft_result.drafted_reply,
            confidence_score=confidence,
            action=action,
        )
        return MessageProcessingResult(response=response, inbound_message=inbound_message, outbound_message=outbound_message)