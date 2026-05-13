# Nistula Guest Message Handler

> An intelligent hospitality API that transforms guest inquiries into prioritized support workflows using AI-powered classification and Claude for smart reply drafting.

## Overview

This FastAPI application powers Nistula's unified messaging platform. It ingests guest messages from multiple channels (WhatsApp, Booking.com, Airbnb, Instagram, direct), classifies them intelligently, drafts contextual replies using Claude, and routes them to the right team member based on confidence scoring.

**Built for**: Real-time guest support at scale  
**Tech Stack**: Python 3.12 + FastAPI + Claude API + PostgreSQL  
**Status**: Production-ready with comprehensive test coverage

---

## What's Included

```
├── app/                      # FastAPI webhook handler & AI integration
│   ├── main.py              # REST endpoint & orchestration 
│   ├── schemas.py           # Pydantic models (validation)
│   ├── classification.py    # Query type detection & confidence scoring
│   ├── claude_client.py     # Claude API client with smart fallbacks
│   └── config.py            # Environment & settings management
├── schema.sql               # PostgreSQL design (guests, messages, audit trail)
├── tests/                   # Test suite with 3 core scenarios
├── thinking.md              # Design thinking responses
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

# Add your Claude API key (get one at console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-api03-..."
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

### 2. **Claude Reply Drafting**
Sends normalized message + property context to Claude, which generates a guest-friendly response:
- Property facts (Villa B1, 3BR, INR 18k/night, etc.)
- Query type & guest context
- Returns professional, on-brand reply

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
If Claude API is unavailable, reply falls back to deterministic templates keyed by query type. System never fails silently.

---

## Testing

Run the test suite to validate all three core scenarios:

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
| `ANTHROPIC_API_KEY` | Yes | — | Claude API key (never commit!) |
| `ANTHROPIC_MODEL` | Optional | `claude-sonnet-4-20250514` | Model version |
| `APP_ENV` | Optional | `development` | Environment label for logs |

**Never commit `.env`** — use `.env.example` as a template.

---

## Confidence Scoring Deep Dive

### Scoring Factors

1. **Base score by query type** (70–91%)
2. **+3% if Claude was used** (vs fallback)
3. **+2% if message is detailed** (≥12 words)
4. **+1% if reply generated successfully**
5. **Capped at 0.59 for complaints** (never auto-send critical issues)

**Example:**
- Query: "Is villa available April 20-24?"
- Type: `pre_sales_availability` (base 0.91)
- Claude used: +0.03 → 0.94
- Final: `auto_send` (≥0.85) 

---

## Database Schema

See [schema.sql](schema.sql) for the PostgreSQL design:
- **guests** — unified guest profiles across all channels
- **reservations** — bookings linked to guests
- **conversations** — channel-specific threads
- **messages** — inbound/outbound with AI metadata
- **message_events** — audit trail (drafted, edited, sent, escalated)

Key design: Keeps operational state on messages for fast reads + maintains full event history for compliance.

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
- Claude API can fail or rate-limit
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

## Part 3 — Design Thinking

See [thinking.md](thinking.md) for detailed responses to:
- **A** — Immediate response to 3am hot water complaint
- **B** — Full system design & escalation workflow
- **C** — Pattern detection for recurring issues

---

## Notes

- API key stored in `.env` (never committed)
- Graceful degradation if Claude is unavailable
- Full audit trail via `message_events` table
- CORS enabled for frontend integration
- Type hints throughout (Python 3.12+)

---

## Questions?

For technical issues, check [thinking.md](thinking.md) or review the well-commented code in `app/main.py`.

---

