import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "messages.db"


def _get_connection() -> sqlite3.Connection:
    """Get a database connection, creating the DB and tables if needed."""
    path = Path(DB_PATH) if isinstance(DB_PATH, str) else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_text TEXT,
            message_type TEXT NOT NULL DEFAULT 'text',
            sent_at TEXT NOT NULL,
            forwarded_to_channels TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at)")
    conn.commit()
    return conn


def save_message(
    user_id: int,
    chat_id: int,
    message_text: Optional[str] = None,
    message_type: str = "text",
    forwarded_channels: Optional[list[int]] = None,
) -> int:
    """Save a message record to the database.

    Returns:
        The ID of the inserted message.
    """
    sent_at = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    cursor = conn.execute(
        """
        INSERT INTO messages
            (user_id, chat_id, message_text, message_type,
             sent_at, forwarded_to_channels)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            chat_id,
            message_text,
            message_type,
            sent_at,
            ",".join(str(c) for c in forwarded_channels)
            if forwarded_channels
            else None,
        ),
    )
    conn.commit()
    message_id = cursor.lastrowid
    conn.close()
    return message_id


def get_messages(
    user_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Query messages from the database.

    Args:
        user_id: Filter by user ID (optional).
        limit: Max results.
        offset: Skip N records.

    Returns:
        List of message dicts.
    """
    conn = _get_connection()
    if user_id:
        cursor = conn.execute(
            """
            SELECT id, user_id, chat_id, message_text,
                   message_type, sent_at, forwarded_to_channels,
                   created_at
            FROM messages
            WHERE user_id = ?
            ORDER BY sent_at DESC
            LIMIT ? OFFSET ?
            """,
            (user_id, limit, offset),
        )
    else:
        cursor = conn.execute(
            """
            SELECT id, user_id, chat_id, message_text,
                   message_type, sent_at, forwarded_to_channels,
                   created_at
            FROM messages
            ORDER BY sent_at DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    messages = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return messages


def get_message_count(user_id: Optional[int] = None) -> int:
    """Get total message count, optionally filtered by user."""
    conn = _get_connection()
    if user_id:
        count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
    else:
        count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    conn.close()
    return count


def get_recent_users(limit: int = 10) -> list[dict]:
    """Get recent unique users with their message count.

    Returns:
        List of dicts with user_id, message_count, last_seen.
    """
    conn = _get_connection()
    cursor = conn.execute(
        """
        SELECT user_id, COUNT(*) as message_count, MAX(sent_at) as last_seen
        FROM messages
        GROUP BY user_id
        ORDER BY last_seen DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    users = [dict(zip(columns, row)) for row in rows]
    conn.close()
    return users
