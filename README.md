# Nistula Guest Message Handler

> A database-backed hospitality operations platform that transforms guest inquiries into prioritized support workflows using AI-powered classification and Gemini for smart reply drafting.

## Overview

This FastAPI application now powers a multi-property unified messaging platform. It ingests guest messages from multiple channels (WhatsApp, Booking.com, Airbnb, Instagram, direct), persists guests, conversations, messages, and audit events, drafts contextual replies using Gemini, and routes them to the right team member based on confidence scoring.

**Built for**: Real-time guest support at scale  
**Tech Stack**: Python 3.12 + FastAPI + SQLAlchemy + SQLite/PostgreSQL + Alembic + Redis/Celery + Gemini API
**Status**: Production-ready foundation with comprehensive test coverage

---

## What's Included

```
├── app/                      # FastAPI app, ORM models, and service layers
│   ├── main.py              # API routes and orchestration 
│   ├── db.py                # SQLAlchemy engine/session helpers
│   ├── models.py            # Guests, properties, conversations, messages
│   ├── schemas.py           # Pydantic models (validation)
│   ├── classification.py    # Query type detection & confidence scoring
│   ├── gemini_client.py     # Gemini API client with smart fallbacks
│   ├── repositories/        # Database access helpers
│   ├── services/            # Message and dashboard workflows
│   └── config.py            # Environment & settings management
├── schema.sql               # PostgreSQL design (guests, messages, audit trail)
├── tests/                   # Test suite with 3 core scenarios
└── requirements.txt         # Dependencies
```

---

## Quick Start

### 1. **Setup**
```bash
# Clone and enter the directory
git clone <repo-url> nistula-technical-assessment
cd nistula-technical-assessment

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Configure Environment**
```bash
# Copy template
cp .env.example .env

# Add your Gemini API key (from Google AI Studio or Vertex AI)
export GEMINI_API_KEY="your-api-key"

# Optional: point to PostgreSQL instead of local SQLite
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/nistula"

# Optional: enable Redis/Celery for background notification jobs
export REDIS_URL="redis://localhost:6379/0"
export CELERY_BROKER_URL="redis://localhost:6379/0"
export CELERY_RESULT_BACKEND="redis://localhost:6379/1"
```

### 3. **Run the API**
```bash
uvicorn app.main:app --reload
```

API is live at http://127.0.0.1:8000

---

## API Endpoint

### POST `/webhook/message`

Receive and process a guest message from any channel.

**Request:**
```json
{
  "source": "whatsapp",
  "guest_name": "Rahul Sharma",
  "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
  "timestamp": "2026-05-05T10:30:00Z",
  "booking_ref": "NIS-2024-0891",
  "property_id": "villa-b1"
}
```

**Response:**
```json
{
  "message_id": "550e8400-e29b-41d4-a716-446655440000",
  "query_type": "pre_sales_availability",
  "drafted_reply": "Hi Rahul! Great news — Villa B1 is available April 20-24. Base rate is INR 18,000/night for up to 4 guests...",
  "confidence_score": 0.91,
  "action": "auto_send"
}
```

### GET `/properties`

Lists the active properties currently served by the platform.

### GET `/dashboard/summary`

Returns a lightweight operations summary for the current day, including message volume, complaints, auto-send rate, and active conversations.

### GET `/dashboard`

Renders the professional operations dashboard with summary cards, property portfolio, recent activity, and live platform signals.

### GET `/conversations/{conversation_id}/messages`

Returns the recent conversation thread for a guest/property conversation.

### POST `/auth/login`

Returns a JWT for demo users such as `owner@nistula.local`.

### GET `/auth/me`

Returns the authenticated user profile.

### GET `/analytics/overview`

Returns message volume, confidence, channel mix, and property usage. Requires `owner` or `manager` role.

### GET `/users`

Lists demo staff users. Requires `owner` or `manager` role.

### GET `/ws/notifications`

Streams live message events to staff dashboards using the JWT passed as `token`.

### GET `/metrics`

Emits lightweight Prometheus-style metrics for operational monitoring.

### POST `/integrations/{channel}/webhook`

Accepts inbound channel payloads from `whatsapp`, `booking_com`, `airbnb`, or `email`, normalizes them, and routes them through the shared AI workflow.

**Try it:**
```bash
curl -X POST http://127.0.0.1:8000/webhook/message \
  -H "Content-Type: application/json" \
  -d '{
    "source": "whatsapp",
    "guest_name": "John Doe",
    "message": "Is the villa available from April 20 to 24?",
    "timestamp": "2026-05-05T10:30:00Z",
    "booking_ref": "TEST-001",
    "property_id": "villa-b1"
  }'
```

---

## How It Works

### 1. **Message Classification**
Detects query intent using pattern matching:
- `pre_sales_availability` — "Is it available on June 5?"
- `pre_sales_pricing` — "What's the rate for 3 nights?"
- `post_sales_checkin` — "What time is check-in?" 
- `special_request` — "Can we do early check-in?"
- `complaint` — "The AC is broken"
- `general_enquiry` — Anything else

### 2. **Gemini Reply Drafting**
Sends normalized message, property context from the database, and recent conversation history to Gemini, which generates a guest-friendly response:
- Property facts (Villa B1, 3BR, INR 18k/night, etc.)
- Query type & guest context
- Returns professional, on-brand reply

The service writes both inbound and outbound records to the database so the next message has context.

### 3. **Confidence Scoring**
Heuristic model determines certainty and routes accordingly:

| Query Type | Base Score | Notes |
|---|---|---|
| pre_sales_availability | 0.91 | Direct answer in context |
| pre_sales_pricing | 0.89 | Pricing rules are explicit |
| post_sales_checkin | 0.84 | High but needs context |
| special_request | 0.76 | Often needs negotiation |
| general_enquiry | 0.71 | Broader scope |
| complaint | 0.48 | Always routed to human |

**Routing Logic:**
```
score >= 0.85 → auto_send (automatic)
0.60 ≤ score < 0.85 → agent_review (human approval)
score < 0.60 → escalate (high priority human)
complaint → escalate (always)
```

### 4. **Graceful Fallback**
If Gemini API is unavailable, reply falls back to deterministic templates keyed by query type. System never fails silently.

### 5. **Persistence Layer**
The app stores:
- guests
- users
- reservations
- conversations
- inbound messages
- outbound drafted replies
- message events for audit history

The app also includes Alembic migrations, a queue-style notification hub with optional Celery fan-out, structured request logging, JWT authentication, RBAC, a live websocket stream, analytics/metrics endpoints, and normalized external channel adapters.

---

## Testing

Run the test suite to validate the webhook workflow and database-backed platform foundation:

```bash
pytest tests/test_webhook.py -v
```

**Test Coverage:**
- Availability inquiry → classified, drafted, auto-sent
- Pricing inquiry → classified, drafted, auto-sent
- Complaint escalation → classified, escalated with human-friendly response

All 3 tests passing confirms end-to-end workflow.

---

## Environment Variables

| Variable | Required | Default | Notes |
|---|---|---|---|
| `GEMINI_API_KEY` | Yes | — | Gemini API key (never commit!) |
| `GEMINI_MODEL` | Optional | `gemini-3-flash` | Model version |
| `DATABASE_URL` | No | `sqlite:///./nistula.db` | SQLite by default, PostgreSQL ready |
| `APP_ENV` | Optional | `development` | Environment label for logs |

**Never commit `.env`** — use `.env.example` as a template.

---

## Confidence Scoring Deep Dive

### Scoring Factors

1. **Base score by query type** (70–91%)
2. **+3% if Gemini was used** (vs fallback)
3. **+2% if message is detailed** (≥12 words)
4. **+1% if reply generated successfully**
5. **Capped at 0.59 for complaints** (never auto-send critical issues)

**Example:**
- Query: "Is villa available April 20-24?"
- Type: `pre_sales_availability` (base 0.91)
- Gemini used: +0.03 → 0.94
- Final: `auto_send` (≥0.85) 

---

## Platform Data

The application uses SQLAlchemy models mirroring the design in [schema.sql](schema.sql):
- **properties** — multi-property context used for reply drafting
- **guests** — unified guest profiles across all channels
- **reservations** — bookings linked to guests
- **conversations** — channel-specific threads
- **messages** — inbound/outbound with AI metadata
- **message_events** — audit trail (drafted, edited, sent, escalated)

Key design: keeps operational state on messages for fast reads while preserving full event history for compliance and debugging.

---

## Design Decisions

### Why Heuristic Scoring Over ML?
- **Interpretable**: Easy to debug and adjust thresholds
- **Fast**: No model inference latency
- **Production-ready**: Works without training data
- **Explainable**: Each score reason is clear to humans

### Why Pattern Matching for Classification?
- Simple and maintainable
- Works without ML training
- Easy to add new patterns as queries evolve
- Fallback to `general_enquiry` is safe

### Why Fallback Replies?
- Gemini API can fail or rate-limit
- Fallback templates are deterministic
- Guests still get a response within SLAs
- No silent failures

---

## API Documentation

Interactive docs available at runtime:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

---

## Development

### Run with auto-reload
```bash
uvicorn app.main:app --reload
```

### Run tests with coverage
```bash
pytest tests/ -v --cov=app
```

### Format code
```bash
black app/ tests/
```

---

## Notes

- API key stored in `.env` (never committed)
- Graceful degradation if Gemini is unavailable
- Full audit trail via `message_events` table
- CORS enabled for frontend integration
- Type hints throughout (Python 3.12+)

---

## Questions?

For technical issues, review the well-commented code in `app/main.py` and the service layers under `app/services/`.

---

