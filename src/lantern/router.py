"""Lantern – brain router with tiered fallback.

Routes requests to cloud (if online + quota available) or local Ollama.
"""

from __future__ import annotations

from lantern.addons.cloud_brains import CloudBrain, RateLimitError
from lantern.addons.ollama_brain import OllamaBrain
from lantern.config import Settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.log import get_logger
from lantern.models import Completion, Msg

log = get_logger("router")


class BrainRouter:
    """Pick the best available brain and generate a completion."""

    def __init__(
        self,
        settings: Settings,
        connectivity: ConnectivityMonitor,
        db: Database,
    ) -> None:
        self._settings = settings
        self._conn = connectivity
        self._db = db
        self._local = OllamaBrain(settings)
        self._clouds: list[CloudBrain] = [
            CloudBrain(p)
            for p in settings.cloud_providers
            if p.api_key
        ]

    async def complete(
        self,
        messages: list[Msg],
        *,
        schema: dict | None = None,
        prefer_cloud: bool = True,
    ) -> Completion:
        """Try cloud providers in order, then fall back to local."""
        # Try cloud if online and preferred
        if prefer_cloud and self._conn.is_online:
            for cloud in self._clouds:
                provider_name = cloud._provider.name
                daily_limit = cloud._provider.daily_limit
                used = self._db.get_quota(provider_name)
                if used >= daily_limit:
                    log.info(
                        "Quota exhausted for %s (%d/%d)",
                        provider_name, used, daily_limit,
                    )
                    continue
                try:
                    result = await cloud.complete(messages, schema=schema)
                    self._db.increment_quota(provider_name)
                    return result
                except RateLimitError as exc:
                    log.warning("Rate limited by %s", exc.provider)
                    continue
                except Exception as exc:
                    log.warning("Cloud %s failed: %s", provider_name, exc)
                    continue

        # Fall back to local
        try:
            return await self._local.complete(messages, schema=schema)
        except ConnectionError:
            log.error("Ollama is unreachable – returning friendly message")
            return Completion(
                text=(
                    "I'm sorry, my local brain (Ollama) isn't responding right now. "
                    "Please check that Ollama is running and try again."
                ),
                model="none",
                provider="none",
                tier="local",
                latency_ms=0,
            )

    @property
    def current_tier(self) -> str:
        if self._conn.is_online and self._clouds:
            return "cloud"
        return "local"

    @property
    def current_model(self) -> str:
        if self._conn.is_online and self._clouds:
            return self._clouds[0].name
        return self._local.name

    async def local_healthy(self) -> bool:
        return await self._local.healthy()
