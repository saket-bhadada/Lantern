"""Lantern – verify-later queue worker.

Runs in the background. When online, picks unverified items from the DB,
sends them to a cloud brain for a second opinion, and posts thread replies.
"""

from __future__ import annotations

import asyncio
import json

from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.log import get_logger
from lantern.models import Msg, QueueItem, Verdict, VerdictChoice
from lantern.router import BrainRouter
from lantern.switch_client import SwitchClient

log = get_logger("verify")

_JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["confirmed", "minor_issue", "incorrect"],
        },
        "corrected_answer": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["verdict", "corrected_answer", "reason"],
    "additionalProperties": False,
}

_JUDGE_SYSTEM = """You are a fact-checker. You will receive a QUESTION and an ANSWER
that was given by a local AI model. Your job is to verify the answer.

Respond with a JSON object:
- verdict: "confirmed" if the answer is accurate, "minor_issue" if mostly right
  but has a small error, "incorrect" if it contains significant errors.
- corrected_answer: if verdict is not "confirmed", provide the corrected answer.
  If confirmed, set to empty string.
- reason: brief explanation of your verdict (1-2 sentences)."""


class VerifyWorker:
    """Background worker that verifies queued answers when online."""

    def __init__(
        self,
        settings: Settings,
        router: BrainRouter,
        connectivity: ConnectivityMonitor,
        db: Database,
        switch: SwitchClient,
    ) -> None:
        self._settings = settings
        self._router = router
        self._conn = connectivity
        self._db = db
        self._switch = switch
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._loop())
        log.info("Verify worker started")

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        while True:
            try:
                if self._conn.is_online:
                    items = self._db.pending_items(limit=5)
                    for item in items:
                        await self._verify_one(item)
                        await asyncio.sleep(self._settings.verify_rate_limit)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.error("Verify worker error: %s", exc)
            await asyncio.sleep(self._settings.verify_rate_limit)

    async def _verify_one(self, item: QueueItem) -> None:
        """Run the judge prompt and post the result."""
        messages = [
            Msg(role="system", content=_JUDGE_SYSTEM),
            Msg(
                role="user",
                content=f"QUESTION:\n{item.question}\n\nANSWER:\n{item.answer}",
            ),
        ]
        try:
            completion = await self._router.complete(
                messages,
                schema=_JUDGE_SCHEMA,
                prefer_cloud=True,
            )
            # Parse structured output
            verdict = self._parse_verdict(completion.text)
            self._db.mark_verified(item.id, verdict)  # type: ignore[arg-type]

            # Post follow-up in thread
            reply_text = self._format_followup(verdict, completion)
            thread = item.root_id or item.thread_id or item.event_id
            await self._switch.send_message(
                item.channel_id,
                reply_text,
                thread_id=thread,
                root_id=thread,
            )
            log.info(
                "Verified item %d: %s", item.id, verdict.verdict.value,
                extra={"event_id": item.event_id},
            )
        except Exception as exc:
            log.error("Failed to verify item %d: %s", item.id, exc)

    def _parse_verdict(self, text: str) -> Verdict:
        """Parse JSON verdict from the judge model, with retry tolerance."""
        # Strip markdown code fences if present
        clean = text.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            clean = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            data = json.loads(clean)
            return Verdict(**data)
        except (json.JSONDecodeError, ValueError):
            log.warning("Could not parse verdict JSON, defaulting to confirmed")
            return Verdict(
                verdict=VerdictChoice.confirmed,
                corrected_answer="",
                reason="Could not parse verification result",
            )

    def _format_followup(self, verdict: Verdict, model_or_comp: str | Completion) -> str:
        if isinstance(model_or_comp, Completion):
            if model_or_comp.tier == "cloud":
                tag = f"☁️ {model_or_comp.model}"
            else:
                tag = f"🧠 local · {model_or_comp.model}"
        else:
            tag = f"☁️ {model_or_comp}"
        if verdict.verdict == VerdictChoice.confirmed:
            return f"✅ Verified online — {verdict.reason}\n\n_{tag}_"
        elif verdict.verdict == VerdictChoice.minor_issue:
            return (
                f"⚠️ Minor correction: {verdict.corrected_answer}\n"
                f"Reason: {verdict.reason}\n\n_{tag}_"
            )
        else:
            return (
                f"⚠️ Correction: {verdict.corrected_answer}\n"
                f"Reason: {verdict.reason}\n\n_{tag}_"
            )
