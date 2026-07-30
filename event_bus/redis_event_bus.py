"""
Redis Pub/Sub concrete implementation of the EventBus.
"""
import asyncio
import json
import logging
from typing import Any, Callable, Coroutine, Dict

from event_bus.base import EventBus
from event_bus.events.base_event import BaseEvent
from integrations.redis.client import RedisClient

logger = logging.getLogger(__name__)


class RedisEventBus(EventBus):
    """
    EventBus using Redis Pub/Sub.
    Enables low-latency decoupled communication inside Covenexa.
    """

    def __init__(self, redis_client: RedisClient) -> None:
        self._client = redis_client
        self._sub_tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start connection (no-op as RedisClient manages its pool)."""
        self._running = True
        logger.info("RedisEventBus started.")

    async def stop(self) -> None:
        """Gracefully stop subscription listeners."""
        self._running = False
        for task in self._sub_tasks:
            task.cancel()
        if self._sub_tasks:
            await asyncio.gather(*self._sub_tasks, return_exceptions=True)
            self._sub_tasks.clear()
        logger.info("RedisEventBus stopped.")

    async def publish(self, event: BaseEvent) -> None:
        """Serialize event to JSON and publish to channel matching class name."""
        channel = event.__class__.__name__
        payload = event.to_dict()
        logger.info("EventBus: publishing event %s to %s", event.event_id, channel)
        await self._client.publish(channel, payload)

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Subscribe to channel and run a background task listening to messages.
        """
        pubsub = await self._client.subscribe(channel)

        async def listen() -> None:
            logger.info("EventBus listener started for channel: %s", channel)
            try:
                # pubsub.listen() yields incoming messages
                async for message in pubsub.listen():
                    if not self._running:
                        break
                    if message["type"] == "message":
                        try:
                            data = json.loads(message["data"])
                            await handler(data)
                        except Exception as exc:
                            logger.error(
                                "EventBus handler failed on channel %s: %s",
                                channel,
                                exc,
                            )
            except asyncio.CancelledError:
                logger.info("EventBus listener for channel %s cancelled.", channel)
            finally:
                await pubsub.unsubscribe(channel)
                await pubsub.close()

        task = asyncio.create_task(listen())
        self._sub_tasks.append(task)
        logger.info("Subscribed to channel: %s", channel)
        
    def get_tasks(self) -> list[asyncio.Task]:
        return self._sub_tasks
