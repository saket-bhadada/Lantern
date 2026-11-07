"""Lantern – connectivity monitor with hysteresis."""

from __future__ import annotations

import asyncio
import time

import httpx

from lantern.config import Settings
from lantern.log import get_logger

log = get_logger("connectivity")

# Number of consecutive successes/failures before flipping state
_HYSTERESIS_UP = 2
_HYSTERESIS_DOWN = 3
_CHECK_INTERVAL = 15.0  # seconds
_PROBE_TARGETS = [
    "https://dns.google/resolve?name=example.com&type=A",
    "https://1.1.1.1/dns-query?name=example.com&type=A",
]


class ConnectivityMonitor:
    """Async monitor that tracks whether we have internet access."""

    def __init__(self, settings: Settings) -> None:
        self._force_offline = settings.force_offline
        self._online = False
        self._consecutive_up = 0
        self._consecutive_down = 0
        self._last_check = 0.0
        self._task: asyncio.Task | None = None

    @property
    def is_online(self) -> bool:
        if self._force_offline:
            return False
        return self._online

    async def start(self) -> None:
        """Start the background polling loop."""
        if self._force_offline:
            log.info("Force-offline mode enabled")
            return
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def check_once(self) -> bool:
        """Run a single connectivity probe. Updates internal state."""
        if self._force_offline:
            return False
        reachable = await self._probe()
        self._update(reachable)
        return self._online

    async def _poll_loop(self) -> None:
        while True:
            await self.check_once()
            await asyncio.sleep(_CHECK_INTERVAL)

    async def _probe(self) -> bool:
        """Try to reach any probe target."""
        for url in _PROBE_TARGETS:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    r = await client.get(url)
                    if r.status_code < 500:
                        return True
            except (httpx.HTTPError, OSError):
                continue
        return False

    def _update(self, reachable: bool) -> None:
        if reachable:
            self._consecutive_up += 1
            self._consecutive_down = 0
            if not self._online and self._consecutive_up >= _HYSTERESIS_UP:
                self._online = True
                log.info("Connectivity: ONLINE")
        else:
            self._consecutive_down += 1
            self._consecutive_up = 0
            if self._online and self._consecutive_down >= _HYSTERESIS_DOWN:
                self._online = False
                log.info("Connectivity: OFFLINE")
            elif not self._online:
                pass  # already offline
