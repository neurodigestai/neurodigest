"""SQLite persistence layer for collected posts."""

import os
import sqlite3
from datetime import datetime, timezone

from constants import DATABASE_PATH
from models import Post
from logger import setup_logger

log = setup_logger()

# ------------------------------------------------------------------ #
# Schema
# ------------------------------------------------------------------ #
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT,
    url          TEXT UNIQUE,
    source       TEXT,
    published    TEXT,
    content_hash TEXT,
    created_at   TEXT
);
"""


def _connect() -> sqlite3.Connection:
    """Return a connection to the SQLite database, creating the
    ``data/`` directory if it does not exist."""
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def initialize_database() -> None:
    """Create the ``posts`` table if it does not already exist.

    Also runs safe migrations (e.g. adding the ``content`` column)
    without losing existing data.
    """
    conn = _connect()
    try:
        conn.execute(_CREATE_TABLE_SQL)
        conn.commit()

        # ── Migration: add content column if missing ──────────────
        try:
            conn.execute("ALTER TABLE posts ADD COLUMN content TEXT")
            conn.commit()
            log.info("Added 'content' column to posts table")
        except sqlite3.OperationalError:
            pass

        # ── Migration: add summary column if missing ─────────────
        try:
            conn.execute("ALTER TABLE posts ADD COLUMN summary TEXT")
            conn.commit()
            log.info("Added 'summary' column to posts table")
        except sqlite3.OperationalError:
            pass

        log.info("Database initialized at %s", DATABASE_PATH)
    finally:
        conn.close()


def post_exists(url: str) -> bool:
    """Return ``True`` if a post with the given *url* is already stored."""
    conn = _connect()
    try:
        cursor = conn.execute("SELECT 1 FROM posts WHERE url = ?", (url,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def insert_post(post: Post) -> bool:
    """Insert a :class:`Post` into the database.

    Returns ``True`` on success, ``False`` if the URL already exists
    (``UNIQUE`` constraint).  Never raises on duplicates.
    """
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO posts (title, url, source, published, content_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                post.title,
                post.url,
                post.source,
                post.published,
                post.content_hash,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate URL — silently skip
        return False
    finally:
        conn.close()


def count_posts() -> int:
    """Return the total number of rows in the ``posts`` table."""
    conn = _connect()
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM posts")
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def get_posts_without_content() -> list[tuple[str, str]]:
    """Return ``(url, source)`` pairs for posts that have no extracted
    content yet."""
    conn = _connect()
    try:
        cursor = conn.execute(
            "SELECT url, source FROM posts WHERE content IS NULL OR content = ''"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def update_post_content(url: str, content: str) -> None:
    """Set the ``content`` field for the post identified by *url*."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE posts SET content = ? WHERE url = ?",
            (content, url),
        )
        conn.commit()
    finally:
        conn.close()


def get_posts_with_content() -> list[dict]:
    """Return all posts that have extracted content as a list of dicts.

    Each dict contains: ``title``, ``url``, ``source``, ``content``.
    """
    conn = _connect()
    try:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT title, url, source, content FROM posts "
            "WHERE content IS NOT NULL AND content != ''"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def get_post_summary(url: str) -> str | None:
    """Return the summary for a post, or ``None`` if not yet summarized."""
    conn = _connect()
    try:
        cursor = conn.execute("SELECT summary FROM posts WHERE url = ?", (url,))
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return None
    finally:
        conn.close()


def update_post_summary(url: str, summary: str) -> None:
    """Set the ``summary`` field for the post identified by *url*."""
    conn = _connect()
    try:
        conn.execute(
            "UPDATE posts SET summary = ? WHERE url = ?",
            (summary, url),
        )
        conn.commit()
    finally:
        conn.close()
