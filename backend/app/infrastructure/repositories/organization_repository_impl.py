"""
PostgreSQL OrganizationRepository implementation using SQLAlchemy ORM.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.organization import Organization
from app.domain.repositories.organization_repository import OrganizationRepository
from app.infrastructure.orm.organization_orm import OrganizationORM


class OrganizationRepositoryImpl(OrganizationRepository):
    """
    Concrete OrganizationRepository implementation using SQLAlchemy async sessions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Organization) -> Organization:
        orm = OrganizationORM.from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.to_entity()

    async def get_by_id(self, id: str) -> Optional[Organization]:
        orm = await self._session.get(OrganizationORM, id)
        return orm.to_entity() if orm else None

    async def get_all(self) -> list[Organization]:
        result = await self._session.execute(select(OrganizationORM))
        return [orm.to_entity() for orm in result.scalars().all()]

    async def update(self, entity: Organization) -> Organization:
        orm = await self._session.get(OrganizationORM, entity.id)
        if not orm:
            raise ValueError(f"Organization with ID {entity.id} does not exist.")
        
        orm.name = entity.name
        orm.industry = entity.industry
        
        await self._session.flush()
        return orm.to_entity()

    async def delete(self, id: str) -> bool:
        orm = await self._session.get(OrganizationORM, id)
        if not orm:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True

    async def get_by_name(self, name: str) -> Optional[Organization]:
        result = await self._session.execute(
            select(OrganizationORM).where(OrganizationORM.name == name)
        )
        orm = result.scalar_one_or_none()
        return orm.to_entity() if orm else None
