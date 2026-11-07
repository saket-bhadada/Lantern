"""Lantern – Cloud brains (OpenAI-compatible endpoints)."""

from __future__ import annotations

import time
import asyncio

import httpx

from lantern.brain import Brain
from lantern.config import CloudProvider
from lantern.log import get_logger
from lantern.models import Completion, Msg

log = get_logger("cloud")

_CLOUD_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


class CloudBrain:
    """Brain implementation for a single OpenAI-compatible cloud provider."""

    tier: str = "cloud"

    def __init__(self, provider: CloudProvider) -> None:
        self._provider = provider
        self.name = f"{provider.name}/{provider.model}"
        self._base = provider.base_url.rstrip("/")

    @property
    def api_key(self) -> str:
        return self._provider.api_key

    async def complete(
        self,
        messages: list[Msg],
        *,
        schema: dict | None = None,
        temperature: float = 0.3,
    ) -> Completion:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        body: dict = {
            "model": self._provider.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
        }
        if schema:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "schema": schema},
            }

        t0 = time.monotonic()
        async with httpx.AsyncClient(timeout=_CLOUD_TIMEOUT) as client:
            resp = await client.post(
                f"{self._base}/chat/completions",
                headers=headers,
                json=body,
            )
            # Handle rate limiting
            if resp.status_code == 429:
                retry_after = int(resp.headers.get("Retry-After", "60"))
                log.warning(
                    "Rate limited by %s, retry after %ds",
                    self._provider.name,
                    retry_after,
                )
                raise RateLimitError(self._provider.name, retry_after)

            resp.raise_for_status()
            data = resp.json()

        elapsed = int((time.monotonic() - t0) * 1000)
        text = data["choices"][0]["message"]["content"]
        log.info(
            "Cloud response",
            extra={
                "model": self._provider.model,
                "latency_ms": elapsed,
                "tier": "cloud",
            },
        )
        return Completion(
            text=text,
            model=self._provider.model,
            provider=self._provider.name,
            tier="cloud",
            latency_ms=elapsed,
        )

    async def healthy(self) -> bool:
        """Check if the API key is set and the endpoint is reachable."""
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(
                    f"{self._base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return r.status_code < 500
        except httpx.HTTPError:
            return False


class RateLimitError(Exception):
    """Raised when a cloud provider returns 429."""

    def __init__(self, provider: str, retry_after: int) -> None:
        self.provider = provider
        self.retry_after = retry_after
        super().__init__(f"{provider} rate limited, retry after {retry_after}s")
