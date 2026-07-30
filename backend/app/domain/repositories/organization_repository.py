"""
Organization repository interface.
"""
from abc import abstractmethod
from typing import Optional
from app.domain.entities.organization import Organization
from app.domain.repositories.base import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    """
    Interface for Organization data access.
    """

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Organization]:
        """Fetch organization profile matching the company name."""
        ...
