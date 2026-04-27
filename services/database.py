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
            edited_text TEXT,
            message_type TEXT NOT NULL DEFAULT 'text',
            forward_immediately INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending',
            sent_at TEXT NOT NULL,
            forwarded_to_channels TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'utc'))
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_sent_at ON messages(sent_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status)")
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
    try:
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
        return message_id
    finally:
        conn.close()


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
    try:
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
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def get_message_count(user_id: Optional[int] = None) -> int:
    """Get total message count, optionally filtered by user."""
    conn = _get_connection()
    try:
        if user_id:
            count = conn.execute(
                "SELECT COUNT(*) FROM messages WHERE user_id = ?",
                (user_id,),
            ).fetchone()[0]
        else:
            count = conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        return count
    finally:
        conn.close()


def get_recent_users(limit: int = 10) -> list[dict]:
    """Get recent unique users with their message count.

    Returns:
        List of dicts with user_id, message_count, last_seen.
    """
    conn = _get_connection()
    try:
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
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def save_server_message(
    text: str,
    user_id: int,
    chat_id: int,
    forward_immediately: bool = True,
) -> int:
    """Save a new message from the API server."""
    sent_at = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO messages
                (user_id, chat_id, message_text, message_type,
                 forward_immediately, status, sent_at)
            VALUES (?, ?, ?, 'text', ?, 'pending', ?)
            """,
            (user_id, chat_id, text, int(forward_immediately), sent_at),
        )
        conn.commit()
        message_id = cursor.lastrowid
        return message_id
    finally:
        conn.close()


def get_messages_with_filters(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """Query messages with optional date and status filters."""
    conn = _get_connection()
    try:
        conditions = []
        params: list = []

        if from_date:
            conditions.append("sent_at >= ?")
            params.append(from_date)
        if to_date:
            conditions.append("sent_at <= ?")
            params.append(to_date)
        if status:
            conditions.append("status = ?")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        cursor = conn.execute(
            f"""
            SELECT id, user_id, chat_id, message_text, edited_text,
                   message_type, forward_immediately, status,
                   sent_at, forwarded_to_channels, created_at
            FROM messages
            {where_clause}
            ORDER BY sent_at DESC
            LIMIT ? OFFSET ?
            """,
            (*params, limit, offset),
        )
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def get_message_by_id(message_id: int) -> Optional[dict]:
    """Get a single message by ID."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT id, user_id, chat_id, message_text, edited_text,
                   message_type, forward_immediately, status,
                   sent_at, forwarded_to_channels, created_at
            FROM messages
            WHERE id = ?
            """,
            (message_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    finally:
        conn.close()


def edit_message(message_id: int, text: str) -> bool:
    """Edit the text of an existing message."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """
            UPDATE messages
            SET edited_text = ?, status = 'pending'
            WHERE id = ?
            """,
            (text, message_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def forward_message(message_id: int, channel_ids: list[int]) -> dict:
    """Mark a message as forwarded and store channel info."""
    channels_str = ",".join(str(c) for c in channel_ids)
    conn = _get_connection()
    try:
        conn.execute(
            """
            UPDATE messages
            SET status = 'forwarded', forwarded_to_channels = ?
            WHERE id = ?
            """,
            (channels_str, message_id),
        )
        conn.commit()
        return {
            "message_id": message_id,
            "status": "forwarded",
            "channel_ids": channel_ids,
        }
    finally:
        conn.close()


def update_message_status(message_id: int, status: str) -> bool:
    """Update the status of a message."""
    conn = _get_connection()
    try:
        conn.execute(
            "UPDATE messages SET status = ? WHERE id = ?",
            (status, message_id),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()
