"""
Abstract memory interface.
Allows storage of session, planner execution, and cross-agent shared states.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseMemory(ABC):
    """
    Abstract memory interface for swappable memory brokers.
    """

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value matching target key."""
        ...

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Retrieve value matching target key."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove key from store."""
        ...
