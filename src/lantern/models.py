"""Lantern – pydantic models shared across all modules."""

from __future__ import annotations

import datetime as _dt
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Chat events (incoming from Switch SSE)
# ---------------------------------------------------------------------------

class ChatEvent(BaseModel):
    """A single chat message received from Switch."""

    id: str = Field(..., description="Unique event / message id for dedup")
    channel_id: str = ""
    channel_name: str = ""
    sender_id: str = ""
    sender_name: str = ""
    text: str = ""
    thread_id: str | None = None
    root_id: str | None = None
    parent_id: str | None = None
    is_mention: bool = False
    is_dm: bool = False
    is_bot: bool = False
    raw: dict = Field(default_factory=dict, description="Original payload")


# ---------------------------------------------------------------------------
# Brain / LLM
# ---------------------------------------------------------------------------

class Msg(BaseModel):
    role: Literal["system", "user", "assistant"] = "user"
    content: str = ""


class Completion(BaseModel):
    text: str = ""
    model: str = ""
    provider: str = ""
    tier: Literal["local", "cloud"] = "local"
    latency_ms: int = 0


# ---------------------------------------------------------------------------
# Reply (outgoing to Switch)
# ---------------------------------------------------------------------------

class Reply(BaseModel):
    text: str = ""
    thread_id: str | None = None
    root_id: str | None = None
    completion: Completion | None = None
    # Postprocessors may attach metadata
    provenance_tag: str = ""
    risk_flagged: bool = False
    queued_for_verification: bool = False


# ---------------------------------------------------------------------------
# Verify queue
# ---------------------------------------------------------------------------

class VerdictChoice(str, Enum):
    confirmed = "confirmed"
    minor_issue = "minor_issue"
    incorrect = "incorrect"


class Verdict(BaseModel):
    verdict: VerdictChoice = VerdictChoice.confirmed
    corrected_answer: str = ""
    reason: str = ""


class QueueItem(BaseModel):
    id: int | None = None
    event_id: str = ""
    channel_id: str = ""
    thread_id: str | None = None
    root_id: str | None = None
    question: str = ""
    answer: str = ""
    model: str = ""
    created_at: str = Field(
        default_factory=lambda: _dt.datetime.now(_dt.timezone.utc).isoformat()
    )
    verified: bool = False
    verdict: Verdict | None = None


# ---------------------------------------------------------------------------
# Teachable rules
# ---------------------------------------------------------------------------

class CorrectionDetection(BaseModel):
    is_correction: bool = False
    proposed_rule: str = Field("", max_length=200)
    scope: str = "global"
    confidence: float = 0.0


class Rule(BaseModel):
    id: str = ""             # e.g. "R-001"
    text: str = ""
    scope: str = "global"
    approver: str = ""
    source_link: str = ""
    date: str = ""
    commit_hash: str = ""
    status: Literal["proposed", "approved", "forgotten"] = "proposed"


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class StatusInfo(BaseModel):
    tier: Literal["local", "cloud", "offline"] = "local"
    online: bool = False
    model: str = ""
    queue_length: int = 0
    cloud_usage_today: dict[str, int] = Field(default_factory=dict)
    active_rules: int = 0
