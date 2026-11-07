"""Tests for Lantern data models."""

from lantern.models import (
    ChatEvent,
    Completion,
    Msg,
    QueueItem,
    Reply,
    Rule,
    Verdict,
    VerdictChoice,
)


def test_chat_event_parsing():
    ev = ChatEvent(
        id="msg-123",
        channel_id="ch-general",
        sender_id="usr-456",
        sender_name="alice",
        text="Hello @lantern what is our deploy policy?",
        is_mention=True,
    )
    assert ev.id == "msg-123"
    assert ev.is_mention is True
    assert ev.is_bot is False


def test_verdict_model():
    v = Verdict(
        verdict=VerdictChoice.minor_issue,
        corrected_answer="Port should be 8065",
        reason="Default Mattermost port is 8065",
    )
    dumped = v.model_dump_json()
    loaded = Verdict.model_validate_json(dumped)
    assert loaded.verdict == VerdictChoice.minor_issue
    assert "8065" in loaded.corrected_answer


def test_rule_model():
    r = Rule(
        id="R-001",
        text="Never deploy on Fridays after 4 PM",
        scope="global",
        approver="alice",
        date="2026-11-07",
    )
    assert r.status == "proposed"
    assert r.id == "R-001"
