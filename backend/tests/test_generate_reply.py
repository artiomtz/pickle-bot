from backend.config import settings
from backend.services.chat_service import generate_reply


def test_generate_reply_dev_mode(monkeypatch):
    monkeypatch.setattr(settings, "is_dev", True)

    reply = generate_reply("hello", "user123", "chat123")
    assert "listen up" in reply
    assert "user123" in reply
    assert "hello" in reply
