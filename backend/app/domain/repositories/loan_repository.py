"""
Loan repository interface.
"""
from abc import abstractmethod
from app.domain.entities.loan import Loan
from app.domain.repositories.base import BaseRepository


class LoanRepository(BaseRepository[Loan]):
    """
    Interface for Loan data access.
    """

    @abstractmethod
    async def get_by_borrower_id(self, borrower_id: str) -> list[Loan]:
        """Fetch all loans matching a borrower ID."""
        ...
