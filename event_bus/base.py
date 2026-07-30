"""
Abstract Event Bus interface.
The concrete implementation (Redis Pub/Sub) is swappable.
Migrating to RabbitMQ or Kafka requires only a new subclass of EventBus.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine

from event_bus.events.base_event import BaseEvent


class EventBus(ABC):
    """
    Abstract Event Bus.

    Decouples producers (e.g. upload handler) from consumers (e.g. Document Agent workflow).
    """

    @abstractmethod
    async def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to the bus.

        Args:
            event: A BaseEvent subclass instance containing the event data.
        """
        ...

    @abstractmethod
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    ) -> None:
        """
        Subscribe to a channel with an async handler.

        Args:
            channel: The event channel name to listen on.
            handler: Async callable that receives the deserialized event dict.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Start the event bus (connect to broker)."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus gracefully."""
        ...
