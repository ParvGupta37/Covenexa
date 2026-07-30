"""
Abstract event handler base class.
"""
from abc import ABC, abstractmethod
from typing import Any
from event_bus.events.base_event import BaseEvent


class BaseHandler(ABC):
    """
    Abstract base for event handlers.
    Subclasses must implement handle() to process incoming events.
    """

    @abstractmethod
    async def handle(self, event_data: dict[str, Any]) -> None:
        """
        Execute processing logic for the event.
        Args:
            event_data: Deserialized raw dictionary representing the event.
        """
        ...
