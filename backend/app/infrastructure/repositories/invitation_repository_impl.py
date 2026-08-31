"""
PostgreSQL InvitationRepository implementation using SQLAlchemy ORM.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.invitation import Invitation
from app.infrastructure.orm.invitation_orm import InvitationORM


class InvitationRepositoryImpl:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: Invitation) -> Invitation:
        orm = InvitationORM.from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.to_entity()

    async def get_by_id(self, id: str) -> Optional[Invitation]:
        orm = await self._session.get(InvitationORM, id)
        return orm.to_entity() if orm else None

    async def get_by_token(self, token: str) -> Optional[Invitation]:
        result = await self._session.execute(
            select(InvitationORM).where(InvitationORM.token == token)
        )
        orm = result.scalar_one_or_none()
        return orm.to_entity() if orm else None

    async def get_by_organization_id(self, organization_id: str) -> list[Invitation]:
        result = await self._session.execute(
            select(InvitationORM)
            .where(InvitationORM.organization_id == organization_id)
            .order_by(InvitationORM.created_at.desc())
        )
        return [orm.to_entity() for orm in result.scalars().all()]

    async def update(self, entity: Invitation) -> Invitation:
        orm = await self._session.get(InvitationORM, entity.id)
        if not orm:
            raise ValueError(f"Invitation with ID {entity.id} does not exist.")
        orm.status = entity.status
        orm.role = entity.role.value if hasattr(entity.role, "value") else str(entity.role)
        orm.name = entity.name
        await self._session.flush()
        return orm.to_entity()

    async def delete(self, id: str) -> bool:
        orm = await self._session.get(InvitationORM, id)
        if not orm:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True
