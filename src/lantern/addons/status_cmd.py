"""Lantern – Status command handler (Phase 3)."""

from __future__ import annotations

import re

from lantern.interfaces import Ctx
from lantern.models import ChatEvent, Reply


class StatusCommandHandler:
    """Replies with current system status, brain tier, queue length, and quotas."""

    trigger = "status"
    approvers_only = False

    async def handle(self, ev: ChatEvent, ctx: Ctx) -> Reply | None:
        text = ev.text.strip().lower()
        cleaned = re.sub(r"@\w+", "", text).strip()
        if cleaned != "status":
            return None

        is_online = ctx.connectivity.is_online
        tier = "cloud" if is_online and ctx.settings.cloud_providers else "local"
        if ctx.settings.force_offline:
            tier_display = "local (forced offline)"
            net_display = "offline (forced)"
        else:
            tier_display = "cloud" if is_online else "local"
            net_display = "online" if is_online else "offline"

        model = (
            ctx.settings.cloud_providers[0].model
            if is_online and ctx.settings.cloud_providers
            else ctx.settings.local_model
        )

        q_len = ctx.db.queue_length()
        quotas = ctx.db.all_quotas_today()
        quota_str = ", ".join(f"{k}: {v}" for k, v in quotas.items()) if quotas else "none"
        active_rules_count = len(ctx.rules.active())

        reply_body = (
            f"**Lantern Status**\n"
            f"- **Network:** {net_display}\n"
            f"- **Active Tier:** {tier_display}\n"
            f"- **Active Model:** `{model}`\n"
            f"- **Verify Queue Length:** {q_len} pending\n"
            f"- **Cloud Usage Today:** {quota_str}\n"
            f"- **Active Rules:** {active_rules_count}"
        )

        return Reply(
            text=reply_body,
            thread_id=ev.thread_id or ev.id,
            root_id=ev.root_id or ev.id,
        )
