"""Tests for BrainRouter tier selection and fallback."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.models import Completion, Msg
from lantern.router import BrainRouter


@pytest.mark.asyncio
async def test_router_local_when_offline():
    settings = Settings(
        local_model="qwen2.5:7b",
        force_offline=True,
    )
    conn = MagicMock(spec=ConnectivityMonitor)
    conn.is_online = False

    db = MagicMock(spec=Database)
    db.get_quota.return_value = 0

    router = BrainRouter(settings, conn, db)
    # Mock local brain
    router._local.complete = AsyncMock(return_value=Completion(
        text="Local answer",
        model="qwen2.5:7b",
        tier="local",
    ))

    res = await router.complete([Msg(role="user", content="hello")])
    assert res.text == "Local answer"
    assert res.tier == "local"
    assert router.current_tier == "local"
