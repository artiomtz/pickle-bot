from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.config import settings
from backend.main import app

client = TestClient(app)


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200

    data = resp.json()
    assert "status" in data
    assert data["status"] == "ok"


def test_auth_missing_key():
    response = client.get("/chats")
    assert response.status_code == 401


def test_auth_invalid_key(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    response = client.get("/chats", headers={"X-API-Key": "wrong"})
    assert response.status_code == 403


def test_auth_valid_key(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    with patch("backend.main.memory_service.get_all_chat_ids") as mock_get:
        mock_get.return_value = ["chat1"]

        response = client.get("/chats", headers={"X-API-Key": "secret"})
        assert response.status_code == 200
        assert response.json() == {"chats": ["chat1"]}


def test_rate_limit_exceeded(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    with patch("backend.main.rate_limiter.allow") as mock_allow:
        mock_allow.return_value = False

        response = client.get("/chats", headers={"X-API-Key": "secret"})
        assert response.status_code == 429


def test_messages_since_validation(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    response = client.get(
        "/messages/since",
        params={"chat_id": "invalid id", "since": "not-a-date"},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 400


def test_messages_since_success(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    with patch("backend.main.memory_service.get_messages_since") as mock_get:
        mock_get.return_value = [("user1", "user", "hello", "2026-08-24T20:00:00Z")]

        response = client.get(
            "/messages/since",
            params={"chat_id": "abc123", "since": "2026-08-24T19:00:00Z"},
            headers={"X-API-Key": "secret"},
        )

        assert response.status_code == 200
        assert response.json()["messages"][0][2] == "hello"


def test_messages_limit_validation(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    response = client.get(
        "/messages/abc123",
        params={"limit": -5},
        headers={"X-API-Key": "secret"},
    )
    assert response.status_code == 400


def test_messages_success(monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")

    with patch("backend.main.memory_service.get_messages") as mock_get:
        mock_get.return_value = [("user1", "user", "hello", "2026-08-24T20:00:00Z")]

        response = client.get(
            "/messages/abc123",
            headers={"X-API-Key": "secret"},
        )

        assert response.status_code == 200
        assert response.json()["messages"][0][2] == "hello"


@patch("backend.main.generate_reply")
def test_chat_endpoint(mock_reply, monkeypatch):
    monkeypatch.setattr(settings, "auth_key", "secret")
    mock_reply.return_value = "burp"

    payload = {
        "message": "hello",
        "chat_id": "abc123",
        "user_id": "user123",
    }

    response = client.post(
        "/chat",
        json=payload,
        headers={"X-API-Key": "secret"},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "burp"
    assert response.json()["chat_id"] == "abc123"
    assert response.json()["user_id"] == "user123"
