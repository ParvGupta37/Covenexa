"""
Loan application command and query handlers.
"""
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.loans.commands import (
    ArchiveLoanCommand,
    CreateLoanCommand,
    DeleteLoanCommand,
    RestoreLoanCommand,
)
from app.application.loans.queries import GetLoanQuery, ListLoansQuery
from app.core.exceptions import DomainException, EntityNotFoundException
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


class ArchiveLoanHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._loan_repo = LoanRepositoryImpl(session)
        self._borrower_repo = BorrowerRepositoryImpl(session)
        self._session = session

    async def handle(self, command: ArchiveLoanCommand) -> Loan:
        loan = await self._loan_repo.get_by_id(command.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", command.loan_id)

        if command.organization_id:
            borrower = await self._borrower_repo.get_by_id(loan.borrower_id)
            if not borrower or borrower.organization_id != command.organization_id:
                raise EntityNotFoundException("Loan", command.loan_id)

        if getattr(loan, "is_archived", False) is True:
            raise DomainException(f"Loan facility '{loan.id}' is already archived.")

        archived = await self._loan_repo.archive(command.loan_id, command.user_id)
        await self._session.commit()
        logger.info("loan.archived", loan_id=command.loan_id, borrower_id=loan.borrower_id)
        return archived


class RestoreLoanHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._loan_repo = LoanRepositoryImpl(session)
        self._borrower_repo = BorrowerRepositoryImpl(session)
        self._session = session

    async def handle(self, command: RestoreLoanCommand) -> Loan:
        loan = await self._loan_repo.get_by_id(command.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", command.loan_id)

        if command.organization_id:
            borrower = await self._borrower_repo.get_by_id(loan.borrower_id)
            if not borrower or borrower.organization_id != command.organization_id:
                raise EntityNotFoundException("Loan", command.loan_id)

        if getattr(loan, "is_archived", False) is not True:
            raise DomainException(f"Loan facility '{loan.id}' is not currently archived.")

        restored = await self._loan_repo.restore(command.loan_id)
        await self._session.commit()
        logger.info("loan.restored", loan_id=command.loan_id, borrower_id=loan.borrower_id)
        return restored


class DeleteLoanHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._loan_repo = LoanRepositoryImpl(session)
        self._borrower_repo = BorrowerRepositoryImpl(session)
        self._session = session

    async def handle(self, command: DeleteLoanCommand) -> bool:
        loan = await self._loan_repo.get_by_id(command.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", command.loan_id)

        if command.organization_id:
            borrower = await self._borrower_repo.get_by_id(loan.borrower_id)
            if not borrower or borrower.organization_id != command.organization_id:
                raise EntityNotFoundException("Loan", command.loan_id)

        success = await self._loan_repo.delete(command.loan_id)
        await self._session.commit()
        logger.info("loan.deleted", loan_id=command.loan_id, borrower_id=loan.borrower_id)
        return success


class LoanQueryHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = LoanRepositoryImpl(session)

    async def get_by_id(self, query: GetLoanQuery) -> Loan:
        loan = await self._repo.get_by_id(query.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", query.loan_id)
        return loan

    async def list_all(self, query: ListLoansQuery) -> list[Loan]:
        status = getattr(query, "status", "ACTIVE")
        if query.borrower_id:
            if status == "ACTIVE":
                return await self._repo.get_by_borrower_id(query.borrower_id)
            return await self._repo.get_by_borrower_id(query.borrower_id, status=status)
        if query.organization_id:
            if status == "ACTIVE":
                return await self._repo.get_by_organization_id(query.organization_id)
            return await self._repo.get_by_organization_id(query.organization_id, status=status)
        if status == "ACTIVE":
            return await self._repo.get_all()
        return await self._repo.get_all(status=status)
