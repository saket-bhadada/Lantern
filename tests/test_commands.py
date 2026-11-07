"""Tests for Lantern command handlers."""

import pytest
from unittest.mock import MagicMock

from lantern.addons.ping_cmd import PingCommandHandler
from lantern.addons.status_cmd import StatusCommandHandler
from lantern.addons.rule_cmds import RulesCommandHandler
from lantern.interfaces import Ctx
from lantern.models import ChatEvent


@pytest.mark.asyncio
async def test_ping_command():
    handler = PingCommandHandler()
    ev = ChatEvent(id="1", text="@lantern ping")
    ctx = MagicMock(spec=Ctx)

    reply = await handler.handle(ev, ctx)
    assert reply is not None
    assert reply.text == "pong"


@pytest.mark.asyncio
async def test_status_command():
    handler = StatusCommandHandler()
    ev = ChatEvent(id="2", text="status")
    ctx = MagicMock()
    ctx.connectivity.is_online = False
    ctx.settings.force_offline = False
    ctx.settings.cloud_providers = []
    ctx.settings.local_model = "qwen2.5:7b"
    ctx.db.queue_length.return_value = 0
    ctx.db.all_quotas_today.return_value = {}
    ctx.rules.active.return_value = []

    reply = await handler.handle(ev, ctx)
    assert reply is not None
    assert "Lantern Status" in reply.text
    assert "qwen2.5:7b" in reply.text
    assert "offline" in reply.text
