"""
PostgreSQL LoanRepository implementation using SQLAlchemy ORM.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.loan import Loan
from app.domain.repositories.loan_repository import LoanRepository
from app.infrastructure.orm.loan_orm import LoanORM


class LoanRepositoryImpl(LoanRepository):
    """
    Concrete LoanRepository implementation using SQLAlchemy async sessions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Loan) -> Loan:
        orm = LoanORM.from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.to_entity()

    async def get_by_id(self, id: str) -> Optional[Loan]:
        orm = await self._session.get(LoanORM, id)
        return orm.to_entity() if orm else None

    async def get_all(self) -> list[Loan]:
        result = await self._session.execute(select(LoanORM))
        return [orm.to_entity() for orm in result.scalars().all()]

    async def update(self, entity: Loan) -> Loan:
        orm = await self._session.get(LoanORM, entity.id)
        if not orm:
            raise ValueError(f"Loan with ID {entity.id} does not exist.")
        
        orm.borrower_id = entity.borrower_id
        orm.agreement_id = entity.agreement_id
        orm.principal_amount = entity.principal_amount.amount
        orm.currency = entity.principal_amount.currency
        orm.interest_rate = entity.interest_rate
        orm.start_date = entity.start_date
        orm.maturity_date = entity.maturity_date
        orm.status = entity.status.value
        
        await self._session.flush()
        return orm.to_entity()

    async def delete(self, id: str) -> bool:
        orm = await self._session.get(LoanORM, id)
        if not orm:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True

    async def get_by_borrower_id(self, borrower_id: str) -> list[Loan]:
        result = await self._session.execute(
            select(LoanORM).where(LoanORM.borrower_id == borrower_id)
        )
        return [orm.to_entity() for orm in result.scalars().all()]
