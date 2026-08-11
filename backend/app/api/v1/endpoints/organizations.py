"""
Organization endpoints.
"""
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role
from app.core.exceptions import EntityAlreadyExistsException
from app.core.schemas.organization import OrganizationCreateSchema, OrganizationResponseSchema
from app.domain.entities.organization import Organization
from app.domain.entities.user import UserRole
from app.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl

router = APIRouter(prefix="/organizations", tags=["Organizations"])


_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.post(
    "/",
    response_model=OrganizationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def create_organization(
    payload: OrganizationCreateSchema,
    session: AsyncSession = Depends(get_db_session),
) -> Organization:
    """Create a new Organization. Restricted to ADMIN role."""
    repo = OrganizationRepositoryImpl(session)

    existing = await repo.get_by_name(payload.name)
    if existing:
        raise EntityAlreadyExistsException("Organization", payload.name)

    org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name,
        industry=payload.industry,
    )
    return await repo.add(org)


@router.get(
    "/",
    response_model=list[OrganizationResponseSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_organizations(session: AsyncSession = Depends(get_db_session)) -> list[Organization]:
    """List all organizations."""
    repo = OrganizationRepositoryImpl(session)
    return await repo.get_all()
