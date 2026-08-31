"""
PostgreSQL BorrowerRepository implementation using SQLAlchemy ORM.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.borrower import Borrower
from app.domain.repositories.borrower_repository import BorrowerRepository
from app.infrastructure.orm.borrower_orm import BorrowerORM


class BorrowerRepositoryImpl(BorrowerRepository):
    """
    Concrete BorrowerRepository implementation using SQLAlchemy async sessions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Borrower) -> Borrower:
        orm = BorrowerORM.from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.to_entity()

    async def get_by_id(self, id: str) -> Optional[Borrower]:
        orm = await self._session.get(BorrowerORM, id)
        return orm.to_entity() if orm else None

    async def get_all(self, status: str = "ACTIVE") -> list[Borrower]:
        query = select(BorrowerORM)
        if status == "ACTIVE":
            query = query.where(BorrowerORM.is_archived == False)
        elif status == "ARCHIVED":
            query = query.where(BorrowerORM.is_archived == True)
        result = await self._session.execute(query)
        return [orm.to_entity() for orm in result.scalars().all()]

    async def update(self, entity: Borrower) -> Borrower:
        orm = await self._session.get(BorrowerORM, entity.id)
        if not orm:
            raise ValueError(f"Borrower with ID {entity.id} does not exist.")
        
        orm.company_name = entity.company_name
        orm.sector = entity.sector
        orm.country = entity.country
        orm.risk_rating_level = entity.risk_rating.level.value
        orm.risk_rating_score = entity.risk_rating.score
        orm.is_archived = entity.is_archived
        orm.archived_at = entity.archived_at
        orm.archived_by = entity.archived_by
        
        await self._session.flush()
        return orm.to_entity()

    async def delete(self, id: str) -> bool:
        orm = await self._session.get(BorrowerORM, id)
        if not orm:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True

    async def get_by_organization_id(
        self, organization_id: str, status: str = "ACTIVE"
    ) -> list[Borrower]:
        query = select(BorrowerORM).where(BorrowerORM.organization_id == organization_id)
        if status == "ACTIVE":
            query = query.where(BorrowerORM.is_archived == False)
        elif status == "ARCHIVED":
            query = query.where(BorrowerORM.is_archived == True)
        result = await self._session.execute(query)
        return [orm.to_entity() for orm in result.scalars().all()]

    async def archive(self, id: str, user_id: str) -> Optional[Borrower]:
        orm = await self._session.get(BorrowerORM, id)
        if not orm:
            return None
        orm.is_archived = True
        orm.archived_at = datetime.now(timezone.utc)
        orm.archived_by = user_id
        await self._session.flush()
        return orm.to_entity()

    async def restore(self, id: str) -> Optional[Borrower]:
        orm = await self._session.get(BorrowerORM, id)
        if not orm:
            return None
        orm.is_archived = False
        orm.archived_at = None
        orm.archived_by = None
        await self._session.flush()
        return orm.to_entity()
