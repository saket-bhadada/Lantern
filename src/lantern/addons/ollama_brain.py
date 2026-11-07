"""Lantern – Ollama brain (local LLM via Ollama HTTP API)."""

from __future__ import annotations

import json
import time

import httpx

from lantern.brain import Brain
from lantern.config import Settings
from lantern.log import get_logger
from lantern.models import Completion, Msg

log = get_logger("ollama")

_OLLAMA_TIMEOUT = httpx.Timeout(120.0, connect=10.0)
_MAX_RETRIES = 2


class OllamaBrain:
    """Brain implementation backed by a local Ollama server."""

    name: str
    tier: str = "local"

    def __init__(self, settings: Settings) -> None:
        self._base = settings.ollama_url.rstrip("/")
        self._model = settings.local_model
        self.name = f"ollama/{self._model}"

    async def complete(
        self,
        messages: list[Msg],
        *,
        schema: dict | None = None,
        temperature: float = 0.3,
    ) -> Completion:
        payload: dict = {
            "model": self._model,
            "messages": [m.model_dump() for m in messages],
            "stream": False,
            "options": {"temperature": temperature},
        }
        if schema:
            payload["format"] = schema

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            t0 = time.monotonic()
            try:
                async with httpx.AsyncClient(
                    base_url=self._base, timeout=_OLLAMA_TIMEOUT
                ) as client:
                    resp = await client.post("/api/chat", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    elapsed = int((time.monotonic() - t0) * 1000)
                    text = data.get("message", {}).get("content", "")
                    log.info(
                        "Ollama response",
                        extra={
                            "model": self._model,
                            "latency_ms": elapsed,
                            "tier": "local",
                        },
                    )
                    return Completion(
                        text=text,
                        model=self._model,
                        provider="ollama",
                        tier="local",
                        latency_ms=elapsed,
                    )
            except (httpx.HTTPError, httpx.StreamError) as exc:
                last_exc = exc
                log.warning(
                    "Ollama attempt %d/%d failed: %s",
                    attempt + 1,
                    _MAX_RETRIES + 1,
                    exc,
                )
                if attempt < _MAX_RETRIES:
                    import asyncio
                    await asyncio.sleep(1.0 * (attempt + 1))

        raise ConnectionError(
            f"Ollama unreachable after {_MAX_RETRIES + 1} attempts: {last_exc}"
        )

    async def healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(f"{self._base}/api/tags")
                return r.status_code == 200
        except httpx.HTTPError:
            return False
