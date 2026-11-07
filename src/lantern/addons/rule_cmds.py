"""Lantern – Rule command handlers (Phase 4).

Handles explicit user actions:
- 'rules': List active rules
- 'teach: <rule>': Propose a new rule
- 'approve <id>': Approve proposed rule (approver only, matched by platform sender_id)
- 'reject <id>': Reject proposed rule (approver only, matched by platform sender_id)
- 'forget <id>': Git-revert an approved rule (approver only, matched by platform sender_id)
"""

from __future__ import annotations

import re

from lantern.interfaces import Ctx
from lantern.models import ChatEvent, Reply


class RulesCommandHandler:
    """Handles commands relating to teachable rules and rule governance."""

    trigger = "rules"
    approvers_only = False

    async def handle(self, ev: ChatEvent, ctx: Ctx) -> Reply | None:
        text = ev.text.strip()
        cleaned = re.sub(r"@\w+", "", text).strip()
        lower = cleaned.lower()

        # 1. 'rules' command
        if lower == "rules":
            active_rules = ctx.rules.active()
            pending = ctx.rules.pending()

            msg_lines = ["**Active Learned Rules:**"]
            if not active_rules:
                msg_lines.append("_No active rules._")
            else:
                for r in active_rules:
                    msg_lines.append(f"- **[{r.id}]** {r.text} _(by {r.approver} on {r.date})_")

            if pending:
                msg_lines.append("\n**Pending Proposals:**")
                for p in pending:
                    msg_lines.append(f"- **[{p.id}]** {p.text} _(awaiting approval)_")

            return Reply(
                text="\n".join(msg_lines),
                thread_id=ev.thread_id or ev.id,
                root_id=ev.root_id or ev.id,
            )

        # 2. 'teach: <rule>'
        teach_match = re.match(r"^teach:\s*(.+)$", cleaned, re.IGNORECASE)
        if teach_match:
            rule_text = teach_match.group(1).strip()
            try:
                proposal = ctx.rules.propose(rule_text, source=f"event:{ev.id}")
                return Reply(
                    text=(
                        f"📝 Proposed rule **{proposal.id}**:\n"
                        f"> {proposal.text}\n\n"
                        f"Approvers can reply `approve {proposal.id}` or `reject {proposal.id}`."
                    ),
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except ValueError as err:
                return Reply(
                    text=f"❌ Could not propose rule: {err}",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )

        # 3. 'approve <id>'
        approve_match = re.match(r"^approve\s+(R-\d+)$", cleaned, re.IGNORECASE)
        if approve_match:
            rule_id = approve_match.group(1).upper()
            try:
                rule = ctx.rules.approve(rule_id, approver_id=ev.sender_id)
                return Reply(
                    text=f"✅ Approved and committed rule **{rule.id}** to `lessons/RULES.md`:\n> {rule.text}",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except PermissionError:
                return Reply(
                    text=f"⛔ Permission denied: User `{ev.sender_id}` is not in the approver allow-list.",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except (KeyError, ValueError) as err:
                return Reply(
                    text=f"❌ Approval failed: {err}",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )

        # 4. 'reject <id>'
        reject_match = re.match(r"^reject\s+(R-\d+)$", cleaned, re.IGNORECASE)
        if reject_match:
            rule_id = reject_match.group(1).upper()
            try:
                ctx.rules.reject(rule_id, approver_id=ev.sender_id)
                return Reply(
                    text=f"🚫 Rejected proposal **{rule_id}**.",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except PermissionError:
                return Reply(
                    text=f"⛔ Permission denied: User `{ev.sender_id}` is not in the approver allow-list.",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except KeyError as err:
                return Reply(
                    text=f"❌ Rejection failed: {err}",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )

        # 5. 'forget <id>'
        forget_match = re.match(r"^forget\s+(R-\d+)$", cleaned, re.IGNORECASE)
        if forget_match:
            rule_id = forget_match.group(1).upper()
            try:
                ctx.rules.forget(rule_id, approver_id=ev.sender_id)
                return Reply(
                    text=f"🧹 Reverted git commit for rule **{rule_id}**. The rule is no longer active.",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except PermissionError:
                return Reply(
                    text=f"⛔ Permission denied: User `{ev.sender_id}` is not in the approver allow-list.",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )
            except KeyError as err:
                return Reply(
                    text=f"❌ Forget failed: {err}",
                    thread_id=ev.thread_id or ev.id,
                    root_id=ev.root_id or ev.id,
                )

        return None
