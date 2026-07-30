"""
Base Event class for Covenexa Event Bus.
All event types must inherit from BaseEvent.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass(kw_only=True)
class BaseEvent:
    """
    Base class for all domain events.
    Includes common metadata fields.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        """
        Serialize event into a JSON-compatible dictionary.
        Override in subclasses if custom serialization is needed.
        """
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.__class__.__name__,
        }
