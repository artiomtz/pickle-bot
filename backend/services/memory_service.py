import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple

from backend.config import settings
from backend.types import Role
from backend.utils.logger_utils import logger
from backend.utils.time_utils import parse_iso_utc, to_iso_utc

DB_PATH = "backend/storage/conversation_memory.db"


class ConversationMemoryService:
    def __init__(
        self,
        db_path: str = DB_PATH,
        max_message_age_days: int = 100,
        max_messages_per_chat: int = 300,
    ):
        self.db_path = db_path
        self.max_message_age_days = max_message_age_days
        self.max_messages_per_chat = max_messages_per_chat
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False, isolation_level=None)
        self._init_schema()

    def _init_schema(self) -> None:
        logger.info("Memory service: initializing schema...")

        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)
        self.conn.commit()
        logger.info("Memory service: schema initiated")

    def enforce_limits(self, chat_id: str) -> None:
        try:
            cutoff_dt = datetime.now(timezone.utc) - timedelta(days=self.max_message_age_days)
            cutoff_iso = cutoff_dt.isoformat()

            logger.info("Memory service cleanup: deleting messages older than %s days for chat %s", self.max_message_age_days, chat_id)
            cursor = self.conn.cursor()

            cursor.execute(
                """
                DELETE FROM messages
                WHERE chat_id = ? AND created_at < ?
                """,
                (chat_id, cutoff_iso),
            )

            logger.info("Memory service cleanup: enforcing max %s messages for chat %s", self.max_messages_per_chat, chat_id)
            cursor.execute(
                """
                SELECT id FROM messages
                WHERE chat_id = ?
                ORDER BY created_at DESC
                LIMIT -1 OFFSET ?
                """,
                (chat_id, self.max_messages_per_chat),
            )

            old_ids = [row[0] for row in cursor.fetchall()]

            if old_ids:
                cursor.execute(
                    f"DELETE FROM messages WHERE id IN ({','.join('?' for _ in old_ids)})",
                    old_ids,
                )
                logger.info("Memory service cleanup: deleted %s old messages for chat %s", len(old_ids), chat_id)

            self.conn.commit()
        except Exception as e:
            logger.error("Memory service cleanup: failed to enforce limits for chat %s: %s", chat_id, e)

    def add_message(self, chat_id: str, user_id: str, role: Role, content: str) -> None:
        try:
            logger.info("Memory service: storing message for chat %s user %s", chat_id, user_id)
            now = datetime.now(timezone.utc).isoformat()

            cursor = self.conn.cursor()
            cursor.execute(
                """INSERT INTO messages (chat_id, user_id, role, content, created_at)
                  VALUES (?, ?, ?, ?, ?)
                  """,
                (chat_id, user_id, role, content, now),
            )
            self.conn.commit()
            logger.info("Memory service: message stored for chat %s user %s", chat_id, user_id)
        except Exception as e:
            logger.error("Memory service: failed to add message for chat %s user %s: %s", chat_id, user_id, e)

    def get_messages(self, chat_id: str, limit: Optional[int] = None) -> List[Tuple[str, str, str, str]]:
        try:
            cursor = self.conn.cursor()

            if limit is not None:
                logger.info("Memory service: retrieving %s latest messages for chat %s", limit, chat_id)
                cursor.execute(
                    """
                    SELECT user_id, role, content, created_at
                    FROM messages
                    WHERE chat_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (chat_id, limit),
                )
                rows = cursor.fetchall()
                rows.reverse()
            else:
                logger.info("Memory service: retrieving all messages for chat %s", chat_id)
                cursor.execute(
                    """
                    SELECT user_id, role, content, created_at
                    FROM messages
                    WHERE chat_id = ?
                    ORDER BY created_at ASC
                    """,
                    (chat_id,),
                )
                rows = cursor.fetchall()

            logger.info("Memory service: retrieved %s messages for chat %s", len(rows), chat_id)
            return rows
        except Exception as e:
            logger.error("Memory service: failed to load messages for chat %s: %s", chat_id, e)
            return []

    def get_messages_since(self, chat_id: str, since_iso: str) -> List[Tuple[str, str, str, str]]:
        try:
            since_dt = parse_iso_utc(since_iso)
            since_iso_norm = to_iso_utc(since_dt)

            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT user_id, role, content, created_at
                FROM messages
                WHERE chat_id = ?
                AND created_at > ?
                ORDER BY created_at ASC
                """,
                (chat_id, since_iso_norm),
            )

            rows = cursor.fetchall()
            logger.info("Memory service: retrieved %s messages since %s for chat %s", len(rows), since_iso_norm, chat_id)
            return rows

        except Exception as e:
            logger.error("Memory service: failed to load messages since %s for chat %s: %s", since_iso, chat_id, e)
            return []

    def get_active_chat_ids(self, days: int = 60) -> List[str]:
        try:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

            cursor = self.conn.cursor()
            cursor.execute(
                """
                SELECT chat_id
                FROM (
                    SELECT chat_id, MAX(created_at) AS last_human_message_at
                    FROM messages
                    WHERE user_id != 'rick'
                    GROUP BY chat_id
                )
                WHERE last_human_message_at >= ?
                """,
                (cutoff,),
            )
            chat_ids = [row[0] for row in cursor.fetchall()]
            logger.info("Memory service: loaded %s active chat ids", len(chat_ids))

            return chat_ids
        except Exception as e:
            logger.error("Memory service: failed to load active chat ids: %s", e)
            return []

    def get_all_chat_ids(self) -> List[str]:
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT DISTINCT chat_id FROM messages")

            rows = cursor.fetchall()
            chat_ids = [row[0] for row in rows]

            logger.info("Memory service: loaded %s chat ids", len(chat_ids))
            return chat_ids

        except Exception as e:
            logger.error("Memory service: failed to load chat ids: %s", e)
            return []

    def clear_all(self) -> None:
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM messages")

            logger.info("Memory service: all messages cleared")
            self.conn.commit()
        except Exception as e:
            logger.error("Memory service: failed to clear all messages: %s", e)


memory_service = ConversationMemoryService(
    max_message_age_days=settings.max_message_age_days,
    max_messages_per_chat=settings.max_messages_per_chat,
)
