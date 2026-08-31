"""
Loan repository interface.
"""
from abc import abstractmethod
from typing import Optional
from app.domain.entities.loan import Loan
from app.domain.repositories.base import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    """
    Interface for Loan data access.
    """

    @abstractmethod
    async def get_by_borrower_id(
        self, borrower_id: str, status: str = "ACTIVE"
    ) -> list[Loan]:
        """Fetch all loans matching a borrower ID filtered by status (ACTIVE, ARCHIVED, ALL)."""
        ...

    @abstractmethod
    async def get_by_organization_id(
        self, organization_id: str, status: str = "ACTIVE"
    ) -> list[Loan]:
        """Fetch all loans matching an organization ID filtered by status (ACTIVE, ARCHIVED, ALL)."""
        ...

    @abstractmethod
    async def archive(self, id: str, user_id: str) -> Optional[Loan]:
        """Mark a loan facility as archived."""
        ...

    @abstractmethod
    async def restore(self, id: str) -> Optional[Loan]:
        """Restore an archived loan facility."""
        ...
