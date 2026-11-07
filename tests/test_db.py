"""Tests for Lantern SQLite database operations."""

import os
import tempfile
from lantern.db import Database
from lantern.models import QueueItem, Verdict, VerdictChoice


def test_queue_and_quota_operations():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db = Database(db_path)
        assert db.queue_length() == 0

        # Enqueue item
        item = QueueItem(
            event_id="ev-1",
            channel_id="ch-test",
            question="What is the port?",
            answer="8080",
            model="qwen2.5:7b",
        )
        row_id = db.enqueue(item)
        assert row_id == 1
        assert db.queue_length() == 1

        pending = db.pending_items(limit=5)
        assert len(pending) == 1
        assert pending[0].question == "What is the port?"

        # Mark verified
        verdict = Verdict(
            verdict=VerdictChoice.minor_issue,
            corrected_answer="8065",
            reason="Mattermost uses 8065",
        )
        db.mark_verified(row_id, verdict)
        assert db.queue_length() == 0

        # Quotas
        assert db.get_quota("gemini") == 0
        db.increment_quota("gemini")
        db.increment_quota("gemini")
        assert db.get_quota("gemini") == 2

        quotas = db.all_quotas_today()
        assert quotas.get("gemini") == 2
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
