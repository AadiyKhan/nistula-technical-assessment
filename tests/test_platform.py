from __future__ import annotations

from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.realtime import notification_hub


client = TestClient(app)


def login(username: str, password: str) -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_and_me():
    token = login("owner@nistula.local", "owner12345")
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "owner"
    assert body["username"] == "owner@nistula.local"


def test_dashboard_page_renders():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Real-time guest operations control" in response.text
    assert "Property portfolio" in response.text


def test_analytics_overview_requires_auth_and_returns_data():
    token = login("manager@nistula.local", "manager12345")
    response = client.get("/analytics/overview", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert "total_messages" in body
    assert "by_channel" in body


def test_websocket_notification_receives_message(monkeypatch):
    notification_hub.drain()
    token = login("support@nistula.local", "support12345")

    monkeypatch.setattr("app.main.get_settings", lambda: SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-3-flash"))
    monkeypatch.setattr(
        "app.main.GeminiDraftClient.draft_reply",
        lambda self, normalized_message, **kwargs: SimpleNamespace(
            drafted_reply="Hi! Villa B1 is available.",
            used_gemini=True,
        ),
    )

    with client.websocket_connect(f"/ws/notifications?token={token}") as websocket:
        payload = {
            "source": "whatsapp",
            "guest_name": "Maya Rao",
            "message": "Is Villa B1 available next week?",
            "timestamp": "2026-05-08T10:00:00Z",
            "booking_ref": "NIS-2024-1001",
            "property_id": "villa-b1",
        }
        response = client.post("/webhook/message", json=payload)
        assert response.status_code == 200
        event = websocket.receive_json()
        assert event["event_type"] == "message_processed"
        assert event["property_id"] == "villa-b1"


def test_whatsapp_integration_webhook(monkeypatch):
    monkeypatch.setattr("app.main.get_settings", lambda: SimpleNamespace(gemini_api_key="test-key", gemini_model="gemini-3-flash"))
    monkeypatch.setattr(
        "app.main.GeminiDraftClient.draft_reply",
        lambda self, normalized_message, **kwargs: SimpleNamespace(
            drafted_reply="Hi Maya! Yes, Villa B1 is available.",
            used_gemini=True,
        ),
    )

    payload = {
        "guest_name": "Maya Rao",
        "text": "Is Villa B1 available next week?",
        "timestamp": "2026-05-08T10:00:00Z",
        "booking_ref": "NIS-2024-1001",
        "property_id": "villa-b1",
        "message_id": "wa-12345",
    }

    response = client.post("/integrations/whatsapp/webhook", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["channel"] == "whatsapp"
    assert body["query_type"] in {"pre_sales_availability", "general_enquiry"}
    assert body["drafted_reply"]
