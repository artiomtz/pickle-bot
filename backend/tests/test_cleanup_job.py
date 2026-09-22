from datetime import datetime, timedelta, timezone

from backend.services.memory_service import ConversationMemoryService
from backend.services.scheduler_service import cleanup_all_chats_job
from backend.types import Role
from backend.utils.time_utils import to_iso_utc


def test_cleanup_job_removes_old_messages(monkeypatch):
    mem = ConversationMemoryService(db_path=":memory:", max_message_age_days=1)

    monkeypatch.setattr("backend.services.scheduler_service.memory_service", mem)

    now = datetime.now(timezone.utc)
    old_time = to_iso_utc(now - timedelta(days=5))
    recent_time = to_iso_utc(now)

    cursor = mem.conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (chat_id, user_id, role, content, created_at)
        VALUES ('chat1', 'user', ?, 'old', ?)
        """,
        (Role.USER, old_time),
    )
    cursor.execute(
        """
        INSERT INTO messages (chat_id, user_id, role, content, created_at)
        VALUES ('chat1', 'user', ?, 'new', ?)
        """,
        (Role.USER, recent_time),
    )
    mem.conn.commit()

    cleanup_all_chats_job()

    rows = mem.get_messages("chat1")
    assert len(rows) == 1
    assert rows[0][2] == "new"
