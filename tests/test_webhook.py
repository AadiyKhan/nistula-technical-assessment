from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class DummyDraftResult(SimpleNamespace):
    pass


def _settings():
    return SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-3-flash")


def test_availability_message(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", _settings)
    monkeypatch.setattr(
        "app.main.GeminiDraftClient.draft_reply",
        lambda self, normalized_message, **kwargs: DummyDraftResult(
            drafted_reply=f"Hi {normalized_message.guest_name.split()[0]}! Yes, Villa B1 is available.",
            used_gemini=True,
        ),
    )

    payload = {
        "source": "whatsapp",
        "guest_name": "Rahul Sharma",
        "message": "Is the villa available from April 20 to 24? What is the rate for 2 adults?",
        "timestamp": "2026-05-05T10:30:00Z",
        "booking_ref": "NIS-2024-0891",
        "property_id": "villa-b1",
    }

    response = client.post("/webhook/message", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["query_type"] == "pre_sales_availability"
    assert body["action"] == "auto_send"
    assert body["confidence_score"] >= 0.85
    assert "available" in body["drafted_reply"].lower()


def test_pricing_message(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", _settings)
    monkeypatch.setattr(
        "app.main.GeminiDraftClient.draft_reply",
        lambda self, normalized_message, **kwargs: DummyDraftResult(
            drafted_reply="Hi! The base rate is INR 18,000 per night.",
            used_gemini=True,
        ),
    )

    payload = {
        "source": "booking_com",
        "guest_name": "Priya Mehta",
        "message": "What is the rate for 2 adults for 3 nights?",
        "timestamp": "2026-05-06T12:00:00Z",
        "booking_ref": "NIS-2024-0892",
        "property_id": "villa-b1",
    }

    response = client.post("/webhook/message", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["query_type"] == "pre_sales_pricing"
    assert body["action"] == "auto_send"
    assert body["confidence_score"] >= 0.85


def test_complaint_escalates(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: SimpleNamespace(gemini_api_key=None, gemini_model="gemini-3-flash"))

    payload = {
        "source": "whatsapp",
        "guest_name": "Arjun Verma",
        "message": "The AC is not working and I am not happy.",
        "timestamp": "2026-05-07T03:00:00Z",
        "booking_ref": "NIS-2024-0893",
        "property_id": "villa-b1",
    }

    response = client.post("/webhook/message", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["query_type"] == "complaint"
    assert body["action"] == "escalate"
    assert body["confidence_score"] < 0.60
    assert "sorry" in body["drafted_reply"].lower()
