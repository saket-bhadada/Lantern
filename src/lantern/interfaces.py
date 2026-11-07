"""Lantern – protocol definitions and context object for extensions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.models import ChatEvent, Completion, Msg, Reply, Rule, Verdict
from lantern.rules import RuleStore


@dataclass
class Ctx:
    """Execution context passed through the pipeline."""
    settings: Settings
    db: Database
    connectivity: ConnectivityMonitor
    rules: RuleStore
    extra: dict[str, Any]


@runtime_checkable
class CommandHandler(Protocol):
    """Handles an explicit command or keyword trigger."""
    trigger: str  # word or prefix, e.g. "status", "rules", "teach:"
    approvers_only: bool

    async def handle(self, ev: ChatEvent, ctx: Ctx) -> Reply | None:
        ...


@runtime_checkable
class Postprocessor(Protocol):
    """Processes or wraps the outgoing reply."""
    order: int

    async def run(self, reply: Reply, ev: ChatEvent, ctx: Ctx) -> Reply:
        ...


@runtime_checkable
class Verifier(Protocol):
    """Second opinion verifier."""
    async def judge(self, question: str, answer: str) -> Verdict:
        ...
