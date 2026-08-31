"""
Borrower endpoints.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.borrowers.commands import (
    ArchiveBorrowerCommand,
    CreateBorrowerCommand,
    DeleteBorrowerCommand,
    RestoreBorrowerCommand,
)
from app.application.borrowers.handlers import (
    ArchiveBorrowerHandler,
    BorrowerQueryHandler,
    CreateBorrowerHandler,
    DeleteBorrowerHandler,
    RestoreBorrowerHandler,
)
from app.application.borrowers.queries import GetBorrowerQuery, ListBorrowersQuery
from app.core.dependencies import get_db_session, get_current_user, require_role
from app.core.exceptions import EntityNotFoundException, ForbiddenException
from app.core.schemas.borrower import BorrowerCreateSchema, BorrowerResponseSchema
from app.domain.entities.borrower import Borrower
from app.domain.entities.user import User, UserRole

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])


_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.post(
    "/",
    response_model=BorrowerResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def create_borrower(
    payload: BorrowerCreateSchema,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Borrower:
    """
    Register a new borrower profile under the authenticated user's organization.
    Available to ADMIN, MANAGER, and ANALYST roles.
    """
    org_id = payload.organization_id
    if current_user.organization_id:
        if org_id and org_id != current_user.organization_id:
            raise ForbiddenException("You cannot register a borrower for another organization.")
        org_id = current_user.organization_id

    command = CreateBorrowerCommand(
        organization_id=org_id,
        company_name=payload.company_name,
        sector=payload.sector,
        country=payload.country,
        risk_level=payload.risk_rating.level,
        risk_score=payload.risk_rating.score,
    )
    handler = CreateBorrowerHandler(session)
    return await handler.handle(command)


@router.get(
    "/",
    response_model=list[BorrowerResponseSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_borrowers(
    organization_id: str | None = None,
    status: str = Query("ACTIVE", pattern="^(ACTIVE|ARCHIVED|ALL)$"),
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Borrower]:
    """
    List borrowers for the user's organization with pagination and lifecycle status filter.
    Default status: 'ACTIVE'.
    """
    limit = max(1, min(500, limit))
    offset = max(0, offset)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    target_org_id = user_org_id or organization_id
    query = ListBorrowersQuery(organization_id=target_org_id, status=status)
    handler = BorrowerQueryHandler(session)
    borrowers = await handler.list_all(query)
    return borrowers[offset: offset + limit]


@router.get(
    "/{borrower_id}",
    response_model=BorrowerResponseSchema,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_borrower(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Borrower:
    """Fetch borrower profile details by ID with tenant verification."""
    query = GetBorrowerQuery(borrower_id=borrower_id)
    handler = BorrowerQueryHandler(session)
    borrower = await handler.get_by_id(query)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You do not have access to this borrower.")

    return borrower


@router.post(
    "/{borrower_id}/archive",
    response_model=BorrowerResponseSchema,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def archive_borrower(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Borrower:
    """
    Archive a borrower profile, removing it from active portfolio operations
    while preserving historical financial metrics, covenants, risk assessments, and audit trails.
    ADMIN only. Enforces strict tenant isolation.
    """
    query = GetBorrowerQuery(borrower_id=borrower_id)
    query_handler = BorrowerQueryHandler(session)
    borrower = await query_handler.get_by_id(query)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot archive a borrower belonging to another organization.")

    command = ArchiveBorrowerCommand(
        borrower_id=borrower_id,
        organization_id=user_org_id or borrower.organization_id,
        user_id=current_user.id,
    )
    handler = ArchiveBorrowerHandler(session)
    archived = await handler.handle(command)

    # Log immutable audit event
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="borrower.archived",
        resource_type="borrower",
        resource_id=borrower_id,
        user_id=current_user.id,
        user_email=current_user.email.value if hasattr(current_user.email, "value") else str(current_user.email),
        details={
            "borrower_id": borrower_id,
            "company_name": borrower.company_name,
            "previous_state": "ACTIVE",
            "new_state": "ARCHIVED",
            "organization_id": borrower.organization_id,
        },
    )
    return archived


@router.post(
    "/{borrower_id}/restore",
    response_model=BorrowerResponseSchema,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def restore_borrower(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Borrower:
    """
    Restore an archived borrower profile back to the active portfolio.
    ADMIN only. Enforces strict tenant isolation.
    """
    query = GetBorrowerQuery(borrower_id=borrower_id)
    query_handler = BorrowerQueryHandler(session)
    borrower = await query_handler.get_by_id(query)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot restore a borrower belonging to another organization.")

    command = RestoreBorrowerCommand(
        borrower_id=borrower_id,
        organization_id=user_org_id or borrower.organization_id,
    )
    handler = RestoreBorrowerHandler(session)
    restored = await handler.handle(command)

    # Log immutable audit event
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="borrower.restored",
        resource_type="borrower",
        resource_id=borrower_id,
        user_id=current_user.id,
        user_email=current_user.email.value if hasattr(current_user.email, "value") else str(current_user.email),
        details={
            "borrower_id": borrower_id,
            "company_name": borrower.company_name,
            "previous_state": "ARCHIVED",
            "new_state": "ACTIVE",
            "organization_id": borrower.organization_id,
        },
    )
    return restored


@router.delete(
    "/{borrower_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def delete_borrower(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Permanently delete a borrower and all associated portfolio data.
    Restricted to organization ADMIN role only.
    Enforces strict tenant isolation.
    """
    query = GetBorrowerQuery(borrower_id=borrower_id)
    query_handler = BorrowerQueryHandler(session)
    borrower = await query_handler.get_by_id(query)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot delete a borrower belonging to another organization.")

    borrower_name = borrower.company_name
    org_id = borrower.organization_id

    # Log audit event before deletion
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="borrower.deleted",
        resource_type="borrower",
        resource_id=borrower_id,
        user_id=current_user.id,
        user_email=current_user.email.value if hasattr(current_user.email, "value") else str(current_user.email),
        details={"company_name": borrower_name, "organization_id": org_id},
    )

    command = DeleteBorrowerCommand(
        borrower_id=borrower_id,
        organization_id=user_org_id or org_id,
    )
    handler = DeleteBorrowerHandler(session)
    await handler.handle(command)
