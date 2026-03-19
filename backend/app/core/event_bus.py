import asyncio
from typing import Any


class EventBus:
    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []

    async def publish(self, event: dict[str, Any]):
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # drop if subscriber can't keep up

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        try:
            self._subscribers.remove(queue)
        except ValueError:
            pass


event_bus = EventBus()
