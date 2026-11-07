"""Lantern – Brain interface and registry."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from lantern.models import Completion, Msg


@runtime_checkable
class Brain(Protocol):
    """Interface for LLM backends (local or cloud)."""

    name: str
    tier: str  # "local" or "cloud"

    async def complete(
        self,
        messages: list[Msg],
        *,
        schema: dict | None = None,
        temperature: float = 0.3,
    ) -> Completion:
        """Generate a completion from messages."""
        ...

    async def healthy(self) -> bool:
        """Return True if the backend is reachable."""
        ...
