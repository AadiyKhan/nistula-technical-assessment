from __future__ import annotations

import asyncio
from queue import Queue, Empty
from typing import Any

from fastapi import WebSocket


class NotificationHub:
    def __init__(self) -> None:
        self._queue: Queue[dict[str, Any]] = Queue()

    def publish(self, event: dict[str, Any]) -> None:
        self._queue.put(event)

    def drain(self) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        while True:
            try:
                drained.append(self._queue.get_nowait())
            except Empty:
                break
        return drained

    async def stream(self, websocket: WebSocket) -> None:
        while True:
            for event in self.drain():
                await websocket.send_json(event)
            await asyncio.sleep(0.2)


notification_hub = NotificationHub()