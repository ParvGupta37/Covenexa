"""
PostgreSQL UserRepository implementation using SQLAlchemy ORM.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.domain.value_objects.email import Email
from app.infrastructure.orm.user_orm import UserORM


class UserRepositoryImpl(UserRepository):
    """
    Concrete UserRepository implementation using SQLAlchemy async sessions.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: User) -> User:
        orm = UserORM.from_entity(entity)
        self._session.add(orm)
        await self._session.flush()
        return orm.to_entity()

    async def get_by_id(self, id: str) -> Optional[User]:
        orm = await self._session.get(UserORM, id)
        return orm.to_entity() if orm else None

    async def get_all(self) -> list[User]:
        result = await self._session.execute(select(UserORM))
        return [orm.to_entity() for orm in result.scalars().all()]

    async def update(self, entity: User) -> User:
        orm = await self._session.get(UserORM, entity.id)
        if not orm:
            raise ValueError(f"User with ID {entity.id} does not exist.")
        
        orm.name = entity.name
        orm.email = str(entity.email)
        orm.password_hash = entity.password_hash
        orm.role = entity.role.value
        
        await self._session.flush()
        return orm.to_entity()

    async def delete(self, id: str) -> bool:
        orm = await self._session.get(UserORM, id)
        if not orm:
            return False
        await self._session.delete(orm)
        await self._session.flush()
        return True

    async def get_by_email(self, email: Email) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.email == str(email))
        )
        orm = result.scalar_one_or_none()
        return orm.to_entity() if orm else None
