"""
User CRUD endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role
from app.core.schemas.user import UserResponseSchema
from app.domain.entities.user import User, UserRole
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/",
    response_model=list[UserResponseSchema],
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))],
)
async def list_users(session: AsyncSession = Depends(get_db_session)) -> list[User]:
    """List all user profiles. Restricted to ADMIN and MANAGER roles."""
    repo = UserRepositoryImpl(session)
    return await repo.get_all()
