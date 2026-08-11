"""
Loan application command and query handlers.
"""
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.loans.commands import CreateLoanCommand
from app.application.loans.queries import GetLoanQuery, ListLoansQuery
from app.core.exceptions import EntityNotFoundException
from app.domain.entities.loan import Loan
from app.domain.value_objects.money import Money
from app.infrastructure.repositories.borrower_repository_impl import BorrowerRepositoryImpl
from app.infrastructure.repositories.loan_repository_impl import LoanRepositoryImpl

logger = structlog.get_logger(__name__)


class CreateLoanHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._loan_repo = LoanRepositoryImpl(session)
        self._borrower_repo = BorrowerRepositoryImpl(session)

    async def handle(self, command: CreateLoanCommand) -> Loan:
        # Verify borrower entity exists
        borrower = await self._borrower_repo.get_by_id(command.borrower_id)
        if not borrower:
            raise EntityNotFoundException("Borrower", command.borrower_id)

        # Money value object validation (amount limits validation)
        principal = Money(amount=command.amount, currency=command.currency)

        loan = Loan(
            id=str(uuid.uuid4()),
            borrower_id=command.borrower_id,
            agreement_id=command.agreement_id,
            principal_amount=principal,
            interest_rate=command.interest_rate,
            start_date=command.start_date,
            maturity_date=command.maturity_date,
            status=command.status,
        )

        result = await self._loan_repo.add(loan)
        await self._loan_repo._session.commit()
        logger.info("loan.created", loan_id=result.id, borrower_id=result.borrower_id)
        return result


class LoanQueryHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LoanRepositoryImpl(session)

    async def get_by_id(self, query: GetLoanQuery) -> Loan:
        loan = await self._repo.get_by_id(query.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", query.loan_id)
        return loan

    async def list_all(self, query: ListLoansQuery) -> list[Loan]:
        if query.borrower_id:
            return await self._repo.get_by_borrower_id(query.borrower_id)
        return await self._repo.get_all()
