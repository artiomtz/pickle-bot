import pytest
from datetime import datetime, timedelta, timezone

from backend.services.memory_service import ConversationMemoryService
from backend.types import Role
from backend.utils.time_utils import to_iso_utc


@pytest.fixture
def mem():
    return ConversationMemoryService(db_path=":memory:")


def test_add_and_get_messages(mem):
    mem.add_message("chat1", "user1", Role.USER, "hello")
    mem.add_message("chat1", "rick", Role.RICK, "burp")

    rows = mem.get_messages("chat1")
    assert len(rows) == 2
    assert rows[0][2] == "hello"
    assert rows[1][2] == "burp"


def test_get_messages_limit(mem):
    for i in range(10):
        mem.add_message("chat1", "user", Role.USER, f"msg{i}")

    rows = mem.get_messages("chat1", limit=3)
    assert len(rows) == 3
    assert rows[0][2] == "msg7"
    assert rows[1][2] == "msg8"
    assert rows[2][2] == "msg9"


def test_get_messages_since(mem):
    now = datetime.now(timezone.utc)
    old_time = to_iso_utc(now - timedelta(hours=3))
    mid_time = to_iso_utc(now - timedelta(hours=1))
    since_time = to_iso_utc(now - timedelta(hours=2))

    cursor = mem.conn.cursor()
    cursor.execute(
        "INSERT INTO messages (chat_id,user_id,role,content,created_at) VALUES ('chat1','user',?, 'old_msg', ?)",
        (Role.USER, old_time),
    )
    cursor.execute(
        "INSERT INTO messages (chat_id,user_id,role,content,created_at) VALUES ('chat1','user',?, 'new_msg', ?)",
        (Role.USER, mid_time),
    )
    mem.conn.commit()

    rows = mem.get_messages_since("chat1", since_time)
    assert len(rows) == 1
    assert rows[0][2] == "new_msg"


def test_get_active_chat_ids(mem):
    now = datetime.now(timezone.utc)
    recent = to_iso_utc(now)
    old = to_iso_utc(now - timedelta(days=10))

    mem.add_message("chat1", "user", Role.USER, "hi")
    mem.add_message("chat2", "rick", Role.RICK, "burp")

    cursor = mem.conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (chat_id, user_id, role, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("chat3", "user", Role.USER, "old", old),
    )
    mem.conn.commit()

    active = mem.get_active_chat_ids(days=5)
    assert "chat1" in active
    assert "chat2" not in active
    assert "chat3" not in active
