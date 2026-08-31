"""
Loan endpoints.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.loans.commands import (
    ArchiveLoanCommand,
    CreateLoanCommand,
    DeleteLoanCommand,
    RestoreLoanCommand,
)
from app.application.loans.handlers import (
    ArchiveLoanHandler,
    CreateLoanHandler,
    DeleteLoanHandler,
    LoanQueryHandler,
    RestoreLoanHandler,
)
from app.application.loans.queries import GetLoanQuery, ListLoansQuery
from app.core.dependencies import get_db_session, get_current_user, require_role
from app.core.exceptions import EntityNotFoundException, ForbiddenException
from app.core.schemas.loan import LoanCreateSchema, LoanResponseSchema
from app.domain.entities.loan import Loan
from app.domain.entities.user import User, UserRole
from app.infrastructure.repositories.borrower_repository_impl import BorrowerRepositoryImpl

router = APIRouter(prefix="/loans", tags=["Loans"])


_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.post(
    "/",
    response_model=LoanResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def create_loan(
    payload: LoanCreateSchema,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """
    Create a new Loan facility. Available to ADMIN, MANAGER, and ANALYST roles.
    Enforces that the borrower belongs to the authenticated user's organization.
    """
    borrower_repo = BorrowerRepositoryImpl(session)
    borrower = await borrower_repo.get_by_id(payload.borrower_id)
    if not borrower:
        raise EntityNotFoundException("Borrower", payload.borrower_id)

    if current_user.organization_id and borrower.organization_id != current_user.organization_id:
        raise ForbiddenException("You cannot create a loan facility for a borrower belonging to another organization.")

    command = CreateLoanCommand(
        borrower_id=payload.borrower_id,
        agreement_id=payload.agreement_id,
        amount=payload.principal_amount.amount,
        currency=payload.principal_amount.currency.upper(),
        interest_rate=payload.interest_rate,
        start_date=payload.start_date,
        maturity_date=payload.maturity_date,
        status=payload.status,
    )
    handler = CreateLoanHandler(session)
    return await handler.handle(command)


@router.get(
    "/",
    response_model=list[LoanResponseSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_loans(
    borrower_id: str | None = None,
    status: str = Query("ACTIVE", pattern="^(ACTIVE|ARCHIVED|ALL)$"),
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Loan]:
    """
    List loans with lifecycle status filter and pagination.
    Strictly isolated to borrowers in the authenticated user's organization.
    """
    limit = max(1, min(500, limit))
    offset = max(0, offset)

    borrower_repo = BorrowerRepositoryImpl(session)
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)

    if borrower_id:
        borrower = await borrower_repo.get_by_id(borrower_id)
        if not borrower or (user_org_id and borrower.organization_id != user_org_id):
            return []
        query = ListLoansQuery(borrower_id=borrower_id, status=status)
        handler = LoanQueryHandler(session)
        loans = await handler.list_all(query)
        return loans[offset: offset + limit]

    # No specific borrower: list loans for all borrowers belonging to the user's organization
    if user_org_id:
        query = ListLoansQuery(organization_id=user_org_id, status=status)
        handler = LoanQueryHandler(session)
        loans = await handler.list_all(query)
        return loans[offset: offset + limit]

    handler = LoanQueryHandler(session)
    loans = await handler.list_all(ListLoansQuery(borrower_id=None, status=status))
    return loans[offset: offset + limit]


@router.get("/count", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_loan_count(
    borrower_id: str | None = None,
    status: str = Query("ACTIVE", pattern="^(ACTIVE|ARCHIVED|ALL)$"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Returns the count of loan facilities for the authenticated organization.
    """
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    
    archive_clause = ""
    if status == "ACTIVE":
        archive_clause = " AND l.is_archived = FALSE"
    elif status == "ARCHIVED":
        archive_clause = " AND l.is_archived = TRUE"

    if borrower_id:
        if user_org_id:
            query = text(f"""
                SELECT COUNT(l.id) FROM loans l
                JOIN borrowers b ON l.borrower_id = b.id
                WHERE l.borrower_id = :b AND b.organization_id = :org_id {archive_clause}
            """)
            result = await session.execute(query, {"b": borrower_id, "org_id": user_org_id})
        else:
            query = text(f"SELECT COUNT(*) FROM loans l WHERE l.borrower_id = :b {archive_clause}")
            result = await session.execute(query, {"b": borrower_id})
    else:
        if user_org_id:
            query = text(f"""
                SELECT COUNT(l.id) FROM loans l
                JOIN borrowers b ON l.borrower_id = b.id
                WHERE b.organization_id = :org_id {archive_clause}
            """)
            result = await session.execute(query, {"org_id": user_org_id})
        else:
            query = text(f"SELECT COUNT(*) FROM loans l WHERE 1=1 {archive_clause}")
            result = await session.execute(query)

    count = result.scalar() or 0
    return {"count": int(count), "borrower_id": borrower_id}


@router.get("/{loan_id}", response_model=LoanResponseSchema, dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_loan(
    loan_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """Fetch loan details by ID with tenant verification."""
    query = GetLoanQuery(loan_id=loan_id)
    handler = LoanQueryHandler(session)
    loan = await handler.get_by_id(query)

    borrower_repo = BorrowerRepositoryImpl(session)
    borrower = await borrower_repo.get_by_id(loan.borrower_id)
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if borrower and user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You do not have access to this loan facility.")

    return loan


@router.post(
    "/{loan_id}/archive",
    response_model=LoanResponseSchema,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def archive_loan(
    loan_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """
    Archive a loan facility, removing it from active portfolio operations
    while preserving historical agreements, covenants, metrics, and audit records.
    ADMIN only. Enforces strict tenant isolation.
    """
    query = GetLoanQuery(loan_id=loan_id)
    handler = LoanQueryHandler(session)
    loan = await handler.get_by_id(query)

    borrower_repo = BorrowerRepositoryImpl(session)
    borrower = await borrower_repo.get_by_id(loan.borrower_id)
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)

    if borrower and user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot archive a loan facility belonging to another organization.")

    command = ArchiveLoanCommand(
        loan_id=loan_id,
        organization_id=user_org_id or (borrower.organization_id if borrower else ""),
        user_id=current_user.id,
    )
    archive_handler = ArchiveLoanHandler(session)
    archived = await archive_handler.handle(command)

    # Log immutable audit event
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="loan.archived",
        resource_type="loan",
        resource_id=loan_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={
            "borrower_id": loan.borrower_id,
            "principal_amount": str(loan.principal_amount.amount),
            "currency": loan.principal_amount.currency,
            "previous_state": "ACTIVE",
            "new_state": "ARCHIVED",
            "organization_id": user_org_id or (borrower.organization_id if borrower else None),
        },
    )
    return archived


@router.post(
    "/{loan_id}/restore",
    response_model=LoanResponseSchema,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def restore_loan(
    loan_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Loan:
    """
    Restore an archived loan facility back to active portfolio monitoring.
    ADMIN only. Enforces strict tenant isolation.
    """
    query = GetLoanQuery(loan_id=loan_id)
    handler = LoanQueryHandler(session)
    loan = await handler.get_by_id(query)

    borrower_repo = BorrowerRepositoryImpl(session)
    borrower = await borrower_repo.get_by_id(loan.borrower_id)
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)

    if borrower and user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot restore a loan facility belonging to another organization.")

    command = RestoreLoanCommand(
        loan_id=loan_id,
        organization_id=user_org_id or (borrower.organization_id if borrower else ""),
    )
    restore_handler = RestoreLoanHandler(session)
    restored = await restore_handler.handle(command)

    # Log immutable audit event
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="loan.restored",
        resource_type="loan",
        resource_id=loan_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={
            "borrower_id": loan.borrower_id,
            "principal_amount": str(loan.principal_amount.amount),
            "currency": loan.principal_amount.currency,
            "previous_state": "ARCHIVED",
            "new_state": "ACTIVE",
            "organization_id": user_org_id or (borrower.organization_id if borrower else None),
        },
    )
    return restored


@router.delete(
    "/{loan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def delete_loan(
    loan_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Permanently delete a loan facility and its associated agreements.
    Restricted to organization ADMIN role only.
    Enforces strict tenant isolation.
    """
    query = GetLoanQuery(loan_id=loan_id)
    handler = LoanQueryHandler(session)
    loan = await handler.get_by_id(query)

    borrower_repo = BorrowerRepositoryImpl(session)
    borrower = await borrower_repo.get_by_id(loan.borrower_id)

    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if borrower and user_org_id and borrower.organization_id != user_org_id:
        raise ForbiddenException("You cannot delete a loan facility belonging to another organization.")

    # Log audit event before deletion
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="loan.deleted",
        resource_type="loan",
        resource_id=loan_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={
            "borrower_id": loan.borrower_id,
            "principal_amount": str(loan.principal_amount.amount),
            "currency": loan.principal_amount.currency,
            "organization_id": user_org_id or (borrower.organization_id if borrower else None),
        },
    )

    command = DeleteLoanCommand(loan_id=loan_id, organization_id=user_org_id)
    delete_handler = DeleteLoanHandler(session)
    await delete_handler.handle(command)
