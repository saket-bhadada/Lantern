"""Lantern – SQLite store for verify queue and cloud quota counters."""

from __future__ import annotations

import datetime as _dt
import json
import sqlite3
import threading
from pathlib import Path

from lantern.log import get_logger
from lantern.models import QueueItem, Verdict, VerdictChoice

log = get_logger("db")


class Database:
    """Thread-safe SQLite wrapper for Lantern's persistent state."""

    def __init__(self, db_path: str = "lantern.db") -> None:
        self._path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS verify_queue (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id    TEXT NOT NULL,
                        channel_id  TEXT NOT NULL,
                        thread_id   TEXT,
                        root_id     TEXT,
                        question    TEXT NOT NULL,
                        answer      TEXT NOT NULL,
                        model       TEXT NOT NULL,
                        created_at  TEXT NOT NULL,
                        verified    INTEGER DEFAULT 0,
                        verdict     TEXT
                    );

                    CREATE TABLE IF NOT EXISTS cloud_quota (
                        provider    TEXT NOT NULL,
                        date        TEXT NOT NULL,
                        count       INTEGER DEFAULT 0,
                        PRIMARY KEY (provider, date)
                    );

                    CREATE TABLE IF NOT EXISTS seen_events (
                        event_id    TEXT PRIMARY KEY,
                        seen_at     TEXT NOT NULL
                    );
                """)
                conn.commit()
            finally:
                conn.close()

    # ------------------------------------------------------------------
    # Verify queue
    # ------------------------------------------------------------------

    def enqueue(self, item: QueueItem) -> int:
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.execute(
                    """INSERT INTO verify_queue
                       (event_id, channel_id, thread_id, root_id,
                        question, answer, model, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        item.event_id, item.channel_id,
                        item.thread_id, item.root_id,
                        item.question, item.answer,
                        item.model, item.created_at,
                    ),
                )
                conn.commit()
                return cur.lastrowid  # type: ignore[return-value]
            finally:
                conn.close()

    def pending_items(self, limit: int = 10) -> list[QueueItem]:
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    """SELECT * FROM verify_queue
                       WHERE verified = 0
                       ORDER BY created_at ASC
                       LIMIT ?""",
                    (limit,),
                ).fetchall()
                return [self._row_to_item(r) for r in rows]
            finally:
                conn.close()

    def mark_verified(self, item_id: int, verdict: Verdict) -> None:
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """UPDATE verify_queue
                       SET verified = 1, verdict = ?
                       WHERE id = ?""",
                    (verdict.model_dump_json(), item_id),
                )
                conn.commit()
            finally:
                conn.close()

    def queue_length(self) -> int:
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) FROM verify_queue WHERE verified = 0"
                ).fetchone()
                return row[0]
            finally:
                conn.close()

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> QueueItem:
        verdict = None
        if row["verdict"]:
            verdict = Verdict.model_validate_json(row["verdict"])
        return QueueItem(
            id=row["id"],
            event_id=row["event_id"],
            channel_id=row["channel_id"],
            thread_id=row["thread_id"],
            root_id=row["root_id"],
            question=row["question"],
            answer=row["answer"],
            model=row["model"],
            created_at=row["created_at"],
            verified=bool(row["verified"]),
            verdict=verdict,
        )

    # ------------------------------------------------------------------
    # Cloud quota
    # ------------------------------------------------------------------

    def increment_quota(self, provider: str) -> int:
        """Increment today's counter for a provider. Returns new count."""
        today = _dt.date.today().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                conn.execute(
                    """INSERT INTO cloud_quota (provider, date, count)
                       VALUES (?, ?, 1)
                       ON CONFLICT(provider, date)
                       DO UPDATE SET count = count + 1""",
                    (provider, today),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT count FROM cloud_quota WHERE provider = ? AND date = ?",
                    (provider, today),
                ).fetchone()
                return row[0] if row else 1
            finally:
                conn.close()

    def get_quota(self, provider: str) -> int:
        """Get today's usage count for a provider."""
        today = _dt.date.today().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                row = conn.execute(
                    "SELECT count FROM cloud_quota WHERE provider = ? AND date = ?",
                    (provider, today),
                ).fetchone()
                return row[0] if row else 0
            finally:
                conn.close()

    def all_quotas_today(self) -> dict[str, int]:
        """Return {provider: count} for today."""
        today = _dt.date.today().isoformat()
        with self._lock:
            conn = self._connect()
            try:
                rows = conn.execute(
                    "SELECT provider, count FROM cloud_quota WHERE date = ?",
                    (today,),
                ).fetchall()
                return {r["provider"]: r["count"] for r in rows}
            finally:
                conn.close()
