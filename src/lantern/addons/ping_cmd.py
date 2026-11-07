"""Lantern – Ping command handler (Phase 1 walking skeleton)."""

from __future__ import annotations

import re

from lantern.interfaces import Ctx
from lantern.models import ChatEvent, Reply


class PingCommandHandler:
    """Replies 'pong' when asked to ping."""

    trigger = "ping"
    approvers_only = False

    async def handle(self, ev: ChatEvent, ctx: Ctx) -> Reply | None:
        text = ev.text.strip().lower()
        # Match 'ping', '@lantern ping', etc.
        cleaned = re.sub(r"@\w+", "", text).strip()
        if cleaned == "ping":
            return Reply(
                text="pong",
                thread_id=ev.thread_id or ev.id,
                root_id=ev.root_id or ev.id,
            )
        return None
