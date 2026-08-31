"""
User repository interface.
"""
from abc import abstractmethod
from typing import Optional
from app.domain.entities.user import User
from app.domain.repositories.base import BaseRepository
from app.domain.value_objects.email import Email


class UserRepository(BaseRepository[User]):
    """
    Interface for User data access.
    """

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Fetch user profile matching the email address."""
        ...

    @abstractmethod
    async def get_by_organization_id(self, organization_id: str) -> list[User]:
        """Fetch all users belonging to the given organization."""
        ...
