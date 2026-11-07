"""Tests for Lantern postprocessors (provenance, risk caution, queueing)."""

import os
import tempfile
import pytest

from lantern.db import Database
from lantern.models import ChatEvent, Completion, Reply
from lantern.postprocessors import (
    ProvenancePostprocessor,
    RiskCautionPostprocessor,
    VerifyQueuePostprocessor,
)


@pytest.mark.asyncio
async def test_provenance_postprocessor():
    prov = ProvenancePostprocessor()
    ev = ChatEvent(id="e1", text="test")
    ctx = {}

    reply = Reply(
        text="The port is 8065",
        completion=Completion(
            text="The port is 8065",
            model="qwen2.5:7b",
            provider="ollama",
            tier="local",
        ),
    )

    processed = await prov.run(reply, ev, ctx)
    assert "_🧠 local · qwen2.5:7b_" in processed.text


@pytest.mark.asyncio
async def test_risk_caution_postprocessor():
    caution = RiskCautionPostprocessor()
    ev = ChatEvent(id="e2", text="how to clean repo")
    ctx = {}

    reply = Reply(
        text="Run rm -rf .git to reset",
        completion=Completion(
            text="Run rm -rf .git to reset",
            model="qwen2.5:7b",
            tier="local",
        ),
    )

    processed = await caution.run(reply, ev, ctx)
    assert processed.risk_flagged is True
    assert "⚠️ _This answer is from my local brain" in processed.text


@pytest.mark.asyncio
async def test_verify_queue_postprocessor():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        queue_proc = VerifyQueuePostprocessor(db)

        ev = ChatEvent(id="e3", channel_id="ch-ops", text="how to reset hard")
        ctx = {}

        reply = Reply(
            text="git reset --hard HEAD~1",
            risk_flagged=True,
            completion=Completion(
                text="git reset --hard HEAD~1",
                model="qwen2.5:7b",
                tier="local",
            ),
        )

        processed = await queue_proc.run(reply, ev, ctx)
        assert processed.queued_for_verification is True
        assert db.queue_length() == 1
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
