"""Lantern – Core message processing pipeline.

Flow: ChatEvent -> Guard -> (CommandHandler | CorrectionDetector | Brain) -> Postprocessors -> Send
"""

from __future__ import annotations

import asyncio
from typing import Any

from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.correction_detector import CorrectionDetector
from lantern.db import Database
from lantern.interfaces import Ctx
from lantern.log import get_logger
from lantern.models import ChatEvent, Msg, Reply
from lantern.prompts import build_system_prompt
from lantern.registry import COMMAND_HANDLERS, POSTPROCESSORS
from lantern.router import BrainRouter
from lantern.rules import RuleStore
from lantern.switch_client import SwitchClient

log = get_logger("engine")


class Engine:
    """The central orchestrator connecting the chat adapter, router, rules, and commands."""

    def __init__(
        self,
        settings: Settings,
        switch: SwitchClient,
        router: BrainRouter,
        connectivity: ConnectivityMonitor,
        db: Database,
        rules: RuleStore,
    ) -> None:
        self.settings = settings
        self.switch = switch
        self.router = router
        self.connectivity = connectivity
        self.db = db
        self.rules = rules

        self.ctx = Ctx(
            settings=settings,
            db=db,
            connectivity=connectivity,
            rules=rules,
            extra={},
        )

        self.command_handlers = [cls() for cls in COMMAND_HANDLERS]
        self.postprocessors = []
        for cls in POSTPROCESSORS:
            # If postprocessor expects db in __init__
            try:
                inst = cls(db)  # type: ignore[call-arg]
            except TypeError:
                inst = cls()
            self.postprocessors.append(inst)
        self.postprocessors.sort(key=lambda p: getattr(p, "order", 100))

        self.correction_detector = CorrectionDetector(router)
        self._known_thread_ids: set[str] = set()

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def guard_passes(self, ev: ChatEvent) -> bool:
        """Filter out messages that should not be processed."""
        # 1. Ignore own messages
        if ev.sender_name.lower() == self.settings.agent_name.lower():
            return False

        # 2. Ignore bot messages
        if ev.is_bot:
            log.debug("Ignored bot message from %s", ev.sender_name)
            return False

        # 3. Channel allow-list
        if self.settings.allowed_channels and ev.channel_id not in self.settings.allowed_channels:
            log.debug("Ignored message in non-allowed channel %s", ev.channel_id)
            return False

        # 4. Trigger check: mention, DM, or participant in thread
        is_in_participating_thread = bool(
            ev.thread_id and ev.thread_id in self._known_thread_ids
        ) or bool(
            ev.root_id and ev.root_id in self._known_thread_ids
        )

        should_reply = ev.is_mention or ev.is_dm or is_in_participating_thread
        return should_reply

    # ------------------------------------------------------------------
    # Pipeline execution
    # ------------------------------------------------------------------

    async def handle_event(self, ev: ChatEvent) -> None:
        """Process a single incoming ChatEvent through the full pipeline."""
        if not self.guard_passes(ev):
            return

        log.info("Processing event %s from %s in channel %s", ev.id, ev.sender_name, ev.channel_id)

        # Record thread participation
        thread_key = ev.root_id or ev.thread_id or ev.id
        self._known_thread_ids.add(thread_key)

        reply: Reply | None = None

        # 1. Try Command Handlers
        for handler in self.command_handlers:
            try:
                res = await handler.handle(ev, self.ctx)
                if res is not None:
                    reply = res
                    break
            except Exception as exc:
                log.error("Command handler error: %s", exc)

        # 2. Check for human correction (if not a command)
        if reply is None:
            # Fast heuristic check before invoking LLM detector: look for correction keywords or thread context
            lower_text = ev.text.lower()
            heuristic_match = any(w in lower_text for w in ["actually", "correction", "incorrect", "wrong", "no,", "rule:"])
            if heuristic_match:
                detection = await self.correction_detector.detect(ev.text)
                if detection.is_correction and detection.confidence >= 0.7 and detection.proposed_rule:
                    try:
                        proposal = self.rules.propose(
                            detection.proposed_rule,
                            source=f"event:{ev.id} sender:{ev.sender_id}",
                        )
                        reply = Reply(
                            text=(
                                f"💡 I noted your correction and drafted rule **{proposal.id}**:\n"
                                f"> {proposal.text}\n\n"
                                f"Approvers can reply `approve {proposal.id}` or `reject {proposal.id}`."
                            ),
                            thread_id=ev.thread_id or ev.id,
                            root_id=ev.root_id or ev.id,
                        )
                    except ValueError as err:
                        log.debug("Proposal duplicate or rejected: %s", err)

        # 3. Brain Completion (standard Q&A)
        if reply is None:
            system_prompt = build_system_prompt(self.rules.rules_for_prompt())
            messages = [
                Msg(role="system", content=system_prompt),
                Msg(role="user", content=ev.text),
            ]

            comp = await self.router.complete(messages, prefer_cloud=True)
            reply = Reply(
                text=comp.text,
                thread_id=ev.thread_id or ev.id,
                root_id=ev.root_id or ev.id,
                completion=comp,
            )

        # 4. Run Postprocessors
        for postproc in self.postprocessors:
            try:
                reply = await postproc.run(reply, ev, self.ctx)
            except Exception as exc:
                log.error("Postprocessor error: %s", exc)

        # 5. Enforce max reply length
        if len(reply.text) > self.settings.max_reply_len:
            reply.text = reply.text[: self.settings.max_reply_len - 20] + "\n...[truncated]"

        # 6. Send to Switch
        success = await self.switch.send_message(
            channel_id=ev.channel_id,
            text=reply.text,
            thread_id=reply.thread_id,
            root_id=reply.root_id,
        )
        if not success:
            log.warning("Failed to send message reply to channel %s", ev.channel_id)
        else:
            # Respect rate limit
            await asyncio.sleep(self.settings.send_rate_limit)
