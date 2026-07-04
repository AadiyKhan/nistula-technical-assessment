"""initial platform schema

Revision ID: 0001_initial_platform
Revises:
Create Date: 2026-07-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_platform"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "properties",
        sa.Column("property_id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("city", sa.String(length=120)),
        sa.Column("base_rate", sa.String(length=80)),
        sa.Column("max_guests", sa.Integer()),
        sa.Column("availability", sa.String(length=120)),
        sa.Column("context_text", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "guests",
        sa.Column("guest_id", sa.String(length=36), primary_key=True),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255)),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="guests_email_unique"),
        sa.UniqueConstraint("phone", name="guests_phone_unique"),
    )

    op.create_table(
        "users",
        sa.Column("user_id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("username", name="users_username_key"),
        sa.CheckConstraint("role IN ('owner', 'manager', 'support', 'housekeeping')", name="users_role_check"),
    )

    op.create_table(
        "reservations",
        sa.Column("reservation_id", sa.String(length=36), primary_key=True),
        sa.Column("booking_ref", sa.String(length=80), nullable=False),
        sa.Column("property_id", sa.String(length=64), nullable=False),
        sa.Column("guest_id", sa.String(length=36), nullable=False),
        sa.Column("check_in_date", sa.Date()),
        sa.Column("check_out_date", sa.Date()),
        sa.Column("reservation_status", sa.String(length=40), nullable=False, server_default="confirmed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.guest_id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"]),
        sa.UniqueConstraint("booking_ref", name="reservations_booking_ref_key"),
    )

    op.create_table(
        "conversations",
        sa.Column("conversation_id", sa.String(length=36), primary_key=True),
        sa.Column("guest_id", sa.String(length=36), nullable=False),
        sa.Column("reservation_id", sa.String(length=36)),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("property_id", sa.String(length=64)),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.guest_id"]),
        sa.ForeignKeyConstraint(["property_id"], ["properties.property_id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.reservation_id"]),
        sa.CheckConstraint("channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')", name="conversations_channel_check"),
    )
    op.create_index("idx_conversations_guest_id", "conversations", ["guest_id"])
    op.create_index("idx_conversations_reservation_id", "conversations", ["reservation_id"])
    op.create_index("idx_conversations_last_message_at", "conversations", ["last_message_at"])

    op.create_table(
        "messages",
        sa.Column("message_id", sa.String(length=36), primary_key=True),
        sa.Column("conversation_id", sa.String(length=36), nullable=False),
        sa.Column("guest_id", sa.String(length=36), nullable=False),
        sa.Column("reservation_id", sa.String(length=36)),
        sa.Column("source_channel", sa.String(length=40), nullable=False),
        sa.Column("direction", sa.String(length=20), nullable=False),
        sa.Column("external_message_id", sa.String(length=120)),
        sa.Column("parent_message_id", sa.String(length=36)),
        sa.Column("message_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text()),
        sa.Column("raw_payload", sa.JSON()),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True)),
        sa.Column("query_type", sa.String(length=80)),
        sa.Column("ai_confidence_score", sa.Float()),
        sa.Column("ai_model", sa.String(length=120)),
        sa.Column("ai_drafted_reply", sa.Text()),
        sa.Column("final_reply_text", sa.Text()),
        sa.Column("workflow_state", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("drafted_by_ai", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("edited_by_agent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("auto_sent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("edited_by_agent_at", sa.DateTime(timezone=True)),
        sa.Column("auto_sent_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.conversation_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["guest_id"], ["guests.guest_id"]),
        sa.ForeignKeyConstraint(["reservation_id"], ["reservations.reservation_id"]),
        sa.ForeignKeyConstraint(["parent_message_id"], ["messages.message_id"]),
        sa.CheckConstraint("source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')", name="messages_source_channel_check"),
        sa.CheckConstraint("direction IN ('inbound', 'outbound')", name="messages_direction_check"),
        sa.CheckConstraint(
            "query_type IS NULL OR query_type IN ('pre_sales_availability', 'pre_sales_pricing', 'post_sales_checkin', 'special_request', 'complaint', 'general_enquiry')",
            name="messages_query_type_check",
        ),
        sa.CheckConstraint("ai_confidence_score IS NULL OR (ai_confidence_score >= 0 AND ai_confidence_score <= 1)", name="messages_confidence_check"),
    )
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id", "received_at"])
    op.create_index("idx_messages_guest_id", "messages", ["guest_id", "received_at"])
    op.create_index("idx_messages_reservation_id", "messages", ["reservation_id"])
    op.create_index("idx_messages_query_type", "messages", ["query_type"])
    op.create_index("idx_messages_workflow_state", "messages", ["workflow_state"])

    op.create_table(
        "message_events",
        sa.Column("message_event_id", sa.String(length=36), primary_key=True),
        sa.Column("message_id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("event_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["messages.message_id"], ondelete="CASCADE"),
        sa.CheckConstraint("event_type IN ('ai_drafted', 'agent_edited', 'auto_sent', 'escalated', 'delivered', 'read')", name="message_events_type_check"),
    )
    op.create_index("idx_message_events_message_id", "message_events", ["message_id", "created_at"])

    op.create_table(
        "notification_events",
        sa.Column("notification_event_id", sa.String(length=36), primary_key=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("notification_events")
    op.drop_index("idx_message_events_message_id", table_name="message_events")
    op.drop_table("message_events")
    op.drop_index("idx_messages_workflow_state", table_name="messages")
    op.drop_index("idx_messages_query_type", table_name="messages")
    op.drop_index("idx_messages_reservation_id", table_name="messages")
    op.drop_index("idx_messages_guest_id", table_name="messages")
    op.drop_index("idx_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_index("idx_conversations_last_message_at", table_name="conversations")
    op.drop_index("idx_conversations_reservation_id", table_name="conversations")
    op.drop_index("idx_conversations_guest_id", table_name="conversations")
    op.drop_table("conversations")
    op.drop_table("reservations")
    op.drop_table("users")
    op.drop_table("guests")
    op.drop_table("properties")
