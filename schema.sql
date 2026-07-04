-- Nistula unified messaging schema
-- Design goals:
-- 1) One guest record across all channels, even if they message from WhatsApp, Airbnb, or direct.
-- 2) One messages table for all inbound and outbound communication.
-- 3) Conversations tie messages to a guest and optionally to a reservation.
-- 4) Audit fields capture whether AI drafted, an agent edited, or the message was auto-sent.
-- 5) Inbound AI metadata stores query type and confidence score on the same row as the message.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE guests (
    guest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT guests_email_unique UNIQUE (email),
    CONSTRAINT guests_phone_unique UNIQUE (phone)
);

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT users_role_check CHECK (role IN ('owner', 'manager', 'support', 'housekeeping'))
);

CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_ref TEXT NOT NULL UNIQUE,
    property_id TEXT NOT NULL,
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    check_in_date DATE,
    check_out_date DATE,
    reservation_status TEXT NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE conversations (
    conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    channel TEXT NOT NULL,
    property_id TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_open BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT conversations_channel_check CHECK (channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct'))
);

CREATE INDEX idx_conversations_guest_id ON conversations (guest_id);
CREATE INDEX idx_conversations_reservation_id ON conversations (reservation_id);
CREATE INDEX idx_conversations_last_message_at ON conversations (last_message_at DESC);

CREATE TABLE messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    guest_id UUID NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    reservation_id UUID REFERENCES reservations(reservation_id) ON DELETE SET NULL,
    source_channel TEXT NOT NULL,
    direction TEXT NOT NULL,
    external_message_id TEXT,
    parent_message_id UUID REFERENCES messages(message_id) ON DELETE SET NULL,
    message_text TEXT NOT NULL,
    normalized_text TEXT,
    raw_payload JSONB,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    query_type TEXT,
    ai_confidence_score NUMERIC(3,2),
    ai_model TEXT,
    ai_drafted_reply TEXT,
    final_reply_text TEXT,
    workflow_state TEXT NOT NULL DEFAULT 'received',
    drafted_by_ai BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by_agent BOOLEAN NOT NULL DEFAULT FALSE,
    auto_sent BOOLEAN NOT NULL DEFAULT FALSE,
    edited_by_agent_at TIMESTAMPTZ,
    auto_sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT messages_source_channel_check CHECK (source_channel IN ('whatsapp', 'booking_com', 'airbnb', 'instagram', 'direct')),
    CONSTRAINT messages_direction_check CHECK (direction IN ('inbound', 'outbound')),
    CONSTRAINT messages_query_type_check CHECK (
        query_type IS NULL OR query_type IN (
            'pre_sales_availability',
            'pre_sales_pricing',
            'post_sales_checkin',
            'special_request',
            'complaint',
            'general_enquiry'
        )
    ),
    CONSTRAINT messages_confidence_check CHECK (ai_confidence_score IS NULL OR (ai_confidence_score >= 0 AND ai_confidence_score <= 1))
);

CREATE INDEX idx_messages_conversation_id ON messages (conversation_id, received_at DESC);
CREATE INDEX idx_messages_guest_id ON messages (guest_id, received_at DESC);
CREATE INDEX idx_messages_reservation_id ON messages (reservation_id);
CREATE INDEX idx_messages_query_type ON messages (query_type);
CREATE INDEX idx_messages_workflow_state ON messages (workflow_state);

CREATE TABLE message_events (
    message_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(message_id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    event_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT message_events_type_check CHECK (
        event_type IN ('ai_drafted', 'agent_edited', 'auto_sent', 'escalated', 'delivered', 'read')
    )
);

CREATE INDEX idx_message_events_message_id ON message_events (message_id, created_at DESC);

CREATE TABLE notification_events (
    notification_event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Hardest design decision:
-- I chose to keep the operational state on messages while also adding message_events for history.
-- That avoids losing the current status during common reads, but still preserves a full audit trail when
-- a message is drafted, edited, escalated, or auto-sent. It is slightly more work than a single status
-- column, but it scales better once multiple agents or automation steps touch the same conversation.
