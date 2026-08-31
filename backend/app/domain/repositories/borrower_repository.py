"""
Borrower repository interface.
"""
from abc import abstractmethod
from typing import Optional
from app.domain.entities.borrower import Borrower
from app.domain.repositories.base import BaseRepository


class BorrowerRepository(BaseRepository[Borrower]):
    """
    Interface for Borrower data access.
    """

    @abstractmethod
    async def get_by_organization_id(
        self, organization_id: str, status: str = "ACTIVE"
    ) -> list[Borrower]:
        """Fetch borrowers belonging to an organization filtered by status (ACTIVE, ARCHIVED, ALL)."""
        ...

    @abstractmethod
    async def archive(self, id: str, user_id: str) -> Optional[Borrower]:
        """Mark a borrower as archived."""
        ...

    @abstractmethod
    async def restore(self, id: str) -> Optional[Borrower]:
        """Restore an archived borrower."""
        ...
