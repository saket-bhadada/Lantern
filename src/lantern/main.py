"""Lantern – Main application entry point."""

from __future__ import annotations

import asyncio
import signal
import sys

from lantern.config import load_settings
from lantern.connectivity import ConnectivityMonitor
from lantern.db import Database
from lantern.engine import Engine
from lantern.log import get_logger, setup_logging
from lantern.router import BrainRouter
from lantern.rules import RuleStore
from lantern.switch_client import SwitchClient
from lantern.verify import VerifyWorker

log = get_logger("main")


async def async_main() -> None:
    settings = load_settings()
    setup_logging(level="INFO", json_output=True)

    log.info(
        "Starting Lantern AI Teammate",
        extra={
            "tier": "init",
            "model": settings.local_model,
        },
    )

    db = Database(settings.db_path)
    rules = RuleStore(settings)
    connectivity = ConnectivityMonitor(settings)
    router = BrainRouter(settings, connectivity, db)
    switch = SwitchClient(settings)
    verify_worker = VerifyWorker(settings, router, connectivity, db, switch)
    engine = Engine(settings, switch, router, connectivity, db, rules)

    await connectivity.start()
    await switch.start()
    await verify_worker.start()

    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        log.info("Shutdown signal received")
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # Windows might not support add_signal_handler for all signals
            pass

    log.info("Lantern is listening for events on Switch...")

    try:
        async for event in switch.listen():
            if stop_event.is_set():
                break
            # Process in background task so SSE listener doesn't block
            asyncio.create_task(engine.handle_event(event))
    except asyncio.CancelledError:
        pass
    finally:
        log.info("Shutting down components...")
        await verify_worker.stop()
        await connectivity.stop()
        await switch.stop()
        log.info("Lantern shutdown complete")


def main() -> None:
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
