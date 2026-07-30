"""
Base Repository Interface.
Uses Generics to establish core CRUD operations.
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Generic repository defining abstract database operations.
    """

    @abstractmethod
    async def add(self, entity: T) -> T:
        """Persist a new entity."""
        ...

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Fetch an entity by its unique ID."""
        ...

    @abstractmethod
    async def get_all(self) -> list[T]:
        """Fetch all instances of this entity."""
        ...

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Remove an entity by ID. Returns True if deleted."""
        ...
