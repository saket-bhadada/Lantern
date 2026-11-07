"""Tests for central Engine pipeline."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.engine import Engine
from lantern.models import ChatEvent, Completion, Msg
from lantern.router import BrainRouter
from lantern.rules import RuleStore
from lantern.switch_client import SwitchClient


@pytest.mark.asyncio
async def test_engine_guard_filters_bot_and_own_messages():
    settings = Settings(agent_name="lantern")
    switch = MagicMock(spec=SwitchClient)
    router = MagicMock(spec=BrainRouter)
    conn = MagicMock(spec=ConnectivityMonitor)
    db = MagicMock(spec=Database)
    rules = MagicMock(spec=RuleStore)

    engine = Engine(settings, switch, router, conn, db, rules)

    # 1. Own message
    ev_own = ChatEvent(id="1", sender_name="lantern", text="test")
    assert engine.guard_passes(ev_own) is False

    # 2. Other bot message
    ev_bot = ChatEvent(id="2", sender_name="otherbot", is_bot=True, text="test")
    assert engine.guard_passes(ev_bot) is False

    # 3. Mention
    ev_mention = ChatEvent(id="3", sender_name="alice", is_mention=True, text="@lantern help")
    assert engine.guard_passes(ev_mention) is True


@pytest.mark.asyncio
async def test_engine_handles_ping_end_to_end():
    settings = Settings(agent_name="lantern", send_rate_limit=0.0)
    switch = MagicMock(spec=SwitchClient)
    switch.send_message = AsyncMock(return_value=True)

    router = MagicMock(spec=BrainRouter)
    conn = MagicMock(spec=ConnectivityMonitor)
    db = MagicMock(spec=Database)
    rules = MagicMock(spec=RuleStore)

    engine = Engine(settings, switch, router, conn, db, rules)

    ev = ChatEvent(id="4", channel_id="ch-demo", sender_name="bob", is_mention=True, text="@lantern ping")
    await engine.handle_event(ev)

    switch.send_message.assert_awaited_once()
    args, kwargs = switch.send_message.await_args
    assert kwargs.get("channel_id") == "ch-demo" or args[0] == "ch-demo"
    assert "pong" in (kwargs.get("text") or args[1])
