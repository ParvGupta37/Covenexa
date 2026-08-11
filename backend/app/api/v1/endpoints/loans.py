"""
Loan endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.loans.commands import CreateLoanCommand
from app.application.loans.handlers import CreateLoanHandler, LoanQueryHandler
from app.application.loans.queries import GetLoanQuery, ListLoansQuery
from app.core.dependencies import get_db_session, require_role
from app.core.schemas.loan import LoanCreateSchema, LoanResponseSchema
from app.domain.entities.loan import Loan
from app.domain.entities.user import UserRole

router = APIRouter(prefix="/loans", tags=["Loans"])


_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.post(
    "/",
    response_model=LoanResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))],
)
async def create_loan(
    payload: LoanCreateSchema,
    session: AsyncSession = Depends(get_db_session),
) -> Loan:
    """Create a new Loan profile. Restricted to ADMIN and MANAGER roles."""
    command = CreateLoanCommand(
        borrower_id=payload.borrower_id,
        agreement_id=payload.agreement_id,
        amount=payload.principal_amount.amount,
        currency=payload.principal_amount.currency,
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
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> list[Loan]:
    """List all loans with pagination. Filter by borrower_id if provided."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    query = ListLoansQuery(borrower_id=borrower_id)
    handler = LoanQueryHandler(session)
    loans = await handler.list_all(query)
    return loans[offset: offset + limit]


@router.get("/count", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_loan_count(
    borrower_id: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Returns the authoritative count of loan facilities from PostgreSQL.
    Used by the dashboard Active Facilities metric.
    Returns {"count": <int>, "borrower_id": <str|null>}.
    Count is always an integer (0 = no facilities, not unavailable).
    """
    if borrower_id:
        result = await session.execute(
            text("SELECT COUNT(*) FROM loans WHERE borrower_id = :b"),
            {"b": borrower_id}
        )
    else:
        result = await session.execute(text("SELECT COUNT(*) FROM loans"))
    count = result.scalar() or 0
    return {"count": int(count), "borrower_id": borrower_id}


@router.get("/{loan_id}", response_model=LoanResponseSchema, dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_loan(
    loan_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Loan:
    """Fetch loan details by ID."""
    query = GetLoanQuery(loan_id=loan_id)
    handler = LoanQueryHandler(session)
    return await handler.get_by_id(query)
