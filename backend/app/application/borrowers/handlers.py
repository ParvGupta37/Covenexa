"""
Borrower application command and query handlers.
"""
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.borrowers.commands import CreateBorrowerCommand
from app.application.borrowers.queries import GetBorrowerQuery, ListBorrowersQuery
from app.core.exceptions import EntityNotFoundException
from app.domain.entities.borrower import Borrower
from app.domain.value_objects.risk_rating import RiskRating
from app.infrastructure.repositories.borrower_repository_impl import BorrowerRepositoryImpl
from app.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl

logger = structlog.get_logger(__name__)


class CreateBorrowerHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._borrower_repo = BorrowerRepositoryImpl(session)
        self._org_repo = OrganizationRepositoryImpl(session)

    async def handle(self, command: CreateBorrowerCommand) -> Borrower:
        # Verify parent organization exists
        org = await self._org_repo.get_by_id(command.organization_id)
        if not org:
            raise EntityNotFoundException("Organization", command.organization_id)

        # Build risk rating value object (validates score ranges internally)
        rating = RiskRating(level=command.risk_level, score=command.risk_score)

        borrower = Borrower(
            id=str(uuid.uuid4()),
            organization_id=command.organization_id,
            company_name=command.company_name,
            sector=command.sector,
            country=command.country,
            risk_rating=rating,
        )

        result = await self._borrower_repo.add(borrower)
        logger.info("borrower.created", borrower_id=result.id, company_name=result.company_name)
        return result


class BorrowerQueryHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = BorrowerRepositoryImpl(session)

    async def get_by_id(self, query: GetBorrowerQuery) -> Borrower:
        borrower = await self._repo.get_by_id(query.borrower_id)
        if not borrower:
            raise EntityNotFoundException("Borrower", query.borrower_id)
        return borrower

    async def list_all(self, query: ListBorrowersQuery) -> list[Borrower]:
        if query.organization_id:
            return await self._repo.get_by_organization_id(query.organization_id)
        return await self._repo.get_all()
