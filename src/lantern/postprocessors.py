"""Lantern – postprocessors (provenance footer, risk caution, queue check)."""

from __future__ import annotations

import re

from lantern.config import Settings
from lantern.db import Database
from lantern.log import get_logger
from lantern.models import ChatEvent, Completion, QueueItem, Reply

log = get_logger("postproc")

# Patterns that suggest a risky answer (commands, numbers, instructions)
_RISK_PATTERNS = [
    re.compile(r"```", re.IGNORECASE),           # code blocks
    re.compile(r"rm\s+-rf", re.IGNORECASE),       # destructive commands
    re.compile(r"git\s+reset\s+--hard", re.IGNORECASE),
    re.compile(r"sudo\s+", re.IGNORECASE),
    re.compile(r"DROP\s+TABLE", re.IGNORECASE),
    re.compile(r"\b\d{3,}\b"),                    # multi-digit numbers (stats/facts)
    re.compile(r"step\s+\d", re.IGNORECASE),      # numbered instructions
]


class ProvenancePostprocessor:
    """Appends a provenance tag to every reply."""

    order = 100

    async def run(self, reply: Reply, ev: ChatEvent, ctx: dict) -> Reply:
        if reply.completion:
            c = reply.completion
            if c.tier == "local":
                reply.provenance_tag = f"🧠 local · {c.model}"
            else:
                reply.provenance_tag = f"☁️ {c.model}" if c.model else f"☁️ {c.provider}"
            reply.text = f"{reply.text}\n\n_{reply.provenance_tag}_"
        return reply


class RiskCautionPostprocessor:
    """Prepends a caution line if the answer looks risky (local-only)."""

    order = 90

    async def run(self, reply: Reply, ev: ChatEvent, ctx: dict) -> Reply:
        if reply.completion and reply.completion.tier == "local":
            for pattern in _RISK_PATTERNS:
                if pattern.search(reply.text):
                    reply.risk_flagged = True
                    reply.text = (
                        "⚠️ _This answer is from my local brain and hasn't been "
                        "verified online yet. Double-check before acting on it._\n\n"
                        + reply.text
                    )
                    break
        return reply


class VerifyQueuePostprocessor:
    """Queues risky local answers for later verification."""

    order = 110

    def __init__(self, db: Database) -> None:
        self._db = db

    async def run(self, reply: Reply, ev: ChatEvent, ctx: dict) -> Reply:
        if (
            reply.completion
            and reply.completion.tier == "local"
            and reply.risk_flagged
        ):
            item = QueueItem(
                event_id=ev.id,
                channel_id=ev.channel_id,
                thread_id=ev.thread_id,
                root_id=ev.root_id,
                question=ev.text,
                answer=reply.completion.text,
                model=reply.completion.model,
            )
            self._db.enqueue(item)
            reply.queued_for_verification = True
            log.info("Queued for verification", extra={"event_id": ev.id})
        return reply
