"""Lantern – Switch Agent Client Protocol (ACP) adapter.

Handles:
- SSE event stream (downstream from switch-core)
- HTTP POST for sending messages (upstream to switch-core)
- Connection heartbeat
- Event deduplication
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import OrderedDict
from typing import AsyncIterator

import httpx

from lantern.config import Settings
from lantern.log import get_logger
from lantern.models import ChatEvent

log = get_logger("switch")

# How many event IDs to keep for dedup
_DEDUP_CAPACITY = 2000


class SwitchClient:
    """Thin async client for the Switch Agent Client Protocol."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._base = settings.switch_core_url.rstrip("/")
        # Switch accepts Bearer authentication for Agent API Keys
        self._headers = {
            "Authorization": f"Bearer {settings.switch_agent_api_key}",
            "Content-Type": "application/json",
        }
        self._seen_ids: OrderedDict[str, None] = OrderedDict()
        self._http: httpx.AsyncClient | None = None
        self._connection_id = str(uuid.uuid4())
        self._beat_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def start(self) -> None:
        self._http = httpx.AsyncClient(
            base_url=self._base,
            headers=self._headers,
            timeout=httpx.Timeout(30.0, connect=10.0),
        )
        log.info("Switch client started", extra={"tier": "switch"})

    async def stop(self) -> None:
        if self._beat_task and not self._beat_task.done():
            self._beat_task.cancel()
        if self._http:
            await self._http.aclose()
            self._http = None
        log.info("Switch client stopped")

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self, agent_name: str, interval: float = 8.0) -> None:
        """Periodically ping Switch Core to keep the connection alive."""
        while True:
            try:
                await asyncio.sleep(interval)
                if self._http:
                    await self._http.post(
                        f"/agents/{agent_name}/connection/beat",
                        json={"connection_id": self._connection_id},
                    )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                log.debug("Heartbeat error: %s", exc)

    # ------------------------------------------------------------------
    # SSE listener
    # ------------------------------------------------------------------

    async def _fetch_room_ids(self) -> list[str]:
        """Fetch all rooms assigned to this agent from Switch."""
        if not self._http:
            return []
        try:
            resp = await self._http.post(
                f"/agents/{self._settings.agent_name}/ops/list_rooms",
                json={},
            )
            if resp.status_code == 200:
                data = resp.json()
                rooms = data.get("result", [])
                return [r["room_id"] for r in rooms if "room_id" in r]
        except Exception as exc:
            log.warning("Could not list rooms: %s", exc)
        return []

    async def listen(self) -> AsyncIterator[ChatEvent]:
        """Yield ChatEvent objects from the Switch SSE stream.

        Reconnects automatically on transient errors.
        """
        agent_name = self._settings.agent_name
        backoff = 1.0

        # Start background heartbeat loop
        if not self._beat_task or self._beat_task.done():
            self._beat_task = asyncio.create_task(
                self._heartbeat_loop(agent_name)
            )

        while True:
            try:
                # Discover rooms assigned to this agent so stream claims them
                room_ids = await self._fetch_room_ids()
                rooms_param = f"&rooms={','.join(room_ids)}" if room_ids else ""

                async with httpx.AsyncClient(
                    base_url=self._base,
                    headers=self._headers,
                    timeout=httpx.Timeout(None, connect=15.0),
                ) as sse_client:
                    log.info("Connecting to SSE stream…", extra={"rooms": len(room_ids)})
                    stream_url = (
                        f"/agents/{agent_name}/events"
                        f"?connection_id={self._connection_id}&scope=all{rooms_param}"
                    )
                    async with sse_client.stream(
                        "GET", stream_url, headers={"Accept": "text/event-stream"}
                    ) as resp:
                        resp.raise_for_status()
                        backoff = 1.0  # reset on success
                        log.info("SSE stream connected", extra={"rooms": room_ids})
                        async for event in self._parse_sse(resp):
                            if event and not self._is_duplicate(event.id):
                                yield event
            except (httpx.HTTPError, httpx.StreamError) as exc:
                log.warning("SSE connection lost: %s – retrying in %.0fs", exc, backoff)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60.0)

    async def _parse_sse(
        self, resp: httpx.Response
    ) -> AsyncIterator[ChatEvent | None]:
        """Parse SSE text/event-stream lines into ChatEvent objects."""
        buffer = ""
        event_type = ""
        async for raw_line in resp.aiter_lines():
            line = raw_line.rstrip("\n").rstrip("\r")
            if line.startswith("event:"):
                event_type = line[6:].strip()
            elif line.startswith("data:"):
                buffer += line[5:].strip()
            elif line == "":
                # End of event block
                if buffer:
                    ev = self._decode_event(event_type, buffer)
                    yield ev
                buffer = ""
                event_type = ""

    def _decode_event(self, event_type: str, data: str) -> ChatEvent | None:
        """Try to parse a JSON data block into a ChatEvent."""
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            log.debug("Non-JSON SSE data: %.100s", data)
            return None

        # Only process message-type events
        if event_type not in ("", "message", "room_message", "chat_message"):
            log.debug("Skipping SSE event type=%s", event_type)
            return None

        agent_name = self._settings.agent_name

        # Handle Switch AgentEvent model: { "room_id": "...", "payload": { "body": "...", ... } }
        inner_payload = payload.get("payload")
        if isinstance(inner_payload, dict):
            text = str(inner_payload.get("body", ""))
            sender_id = str(inner_payload.get("sender", ""))
            sender_name = str(inner_payload.get("sender_name", ""))
            sender_kind = str(inner_payload.get("sender_kind", "user"))
            channel_id = str(payload.get("room_id", ""))
            event_id = str(inner_payload.get("message_id", f"ev-{time.time()}"))
            thread_id = inner_payload.get("thread_id")
            addressed = bool(inner_payload.get("addressed", False))
            is_bot = sender_kind == "agent"
        else:
            msg = payload.get("message", payload)
            sender = payload.get("sender", {})
            text = msg.get("text", "") if isinstance(msg, dict) else str(msg)
            sender_id = str(sender.get("id", sender.get("user_id", "")))
            sender_name = str(sender.get("name", sender.get("username", "")))
            channel_id = str(payload.get("channel_id", payload.get("room_id", "")))
            event_id = str(payload.get("id", payload.get("message_id", f"ev-{time.time()}")))
            thread_id = payload.get("thread_id")
            addressed = False
            is_bot = bool(sender.get("is_bot", False))

        is_mention = addressed or (f"@{agent_name}" in text.lower())

        event = ChatEvent(
            id=event_id,
            channel_id=channel_id,
            channel_name=str(payload.get("channel_name", "")),
            sender_id=sender_id,
            sender_name=sender_name,
            text=text,
            thread_id=thread_id,
            root_id=payload.get("root_id"),
            parent_id=payload.get("parent_id"),
            is_mention=is_mention,
            is_dm=bool(payload.get("is_dm", False)),
            is_bot=is_bot,
            raw=payload,
        )
        return event

    def _is_duplicate(self, event_id: str) -> bool:
        if event_id in self._seen_ids:
            return True
        self._seen_ids[event_id] = None
        if len(self._seen_ids) > _DEDUP_CAPACITY:
            self._seen_ids.popitem(last=False)
        return False

    # ------------------------------------------------------------------
    # Send message
    # ------------------------------------------------------------------

    async def send_message(
        self,
        channel_id: str,
        text: str,
        *,
        thread_id: str | None = None,
        root_id: str | None = None,
    ) -> bool:
        """Post a message to a Switch room. Returns True on success."""
        if not self._http:
            log.error("Cannot send – client not started")
            return False

        agent_name = self._settings.agent_name
        body = {
            "room_id": channel_id,
            "content": text,
        }
        if thread_id or root_id:
            body["metadata"] = {}
            if thread_id:
                body["metadata"]["thread_id"] = thread_id
            if root_id:
                body["metadata"]["root_id"] = root_id

        try:
            # Switch API route for sending messages
            resp = await self._http.post(
                f"/agents/{agent_name}/message",
                json=body,
            )
            if resp.status_code >= 400:
                log.error(
                    "Send failed: %d %s",
                    resp.status_code,
                    resp.text[:200],
                    extra={"channel": channel_id},
                )
                return False
            log.info(
                "Message sent",
                extra={"channel": channel_id, "tier": "switch"},
            )
            return True
        except httpx.HTTPError as exc:
            log.error("Send error: %s", exc, extra={"channel": channel_id})
            return False

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    async def healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(f"{self._base}/health/ready")
                return r.status_code == 200
        except httpx.HTTPError:
            return False
