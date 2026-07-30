"""
Borrower repository interface.
"""
from abc import abstractmethod
from app.domain.entities.borrower import Borrower
from app.domain.repositories.base import BaseRepository


class BorrowerRepository(BaseRepository[Borrower]):
    """
    Interface for Borrower data access.
    """

    @abstractmethod
    async def get_by_organization_id(self, organization_id: str) -> list[Borrower]:
        """Fetch all borrowers belonging to an organization."""
        ...
