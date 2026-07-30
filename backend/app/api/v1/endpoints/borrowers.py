"""
Borrower endpoints.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.borrowers.commands import CreateBorrowerCommand
from app.application.borrowers.handlers import BorrowerQueryHandler, CreateBorrowerHandler
from app.application.borrowers.queries import GetBorrowerQuery, ListBorrowersQuery
from app.core.dependencies import get_db_session, require_role
from app.core.schemas.borrower import BorrowerCreateSchema, BorrowerResponseSchema
from app.domain.entities.borrower import Borrower
from app.domain.entities.user import UserRole

router = APIRouter(prefix="/borrowers", tags=["Borrowers"])


@router.post(
    "/",
    response_model=BorrowerResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.MANAGER]))],
)
async def create_borrower(
    payload: BorrowerCreateSchema,
    session: AsyncSession = Depends(get_db_session),
) -> Borrower:
    """Register a new borrower profile. Restricted to ADMIN and MANAGER roles."""
    command = CreateBorrowerCommand(
        organization_id=payload.organization_id,
        company_name=payload.company_name,
        sector=payload.sector,
        country=payload.country,
        risk_level=payload.risk_rating.level,
        risk_score=payload.risk_rating.score,
    )
    handler = CreateBorrowerHandler(session)
    return await handler.handle(command)


@router.get("/", response_model=list[BorrowerResponseSchema])
async def list_borrowers(
    organization_id: str | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> list[Borrower]:
    """List all borrowers. Filter by organization_id if provided."""
    query = ListBorrowersQuery(organization_id=organization_id)
    handler = BorrowerQueryHandler(session)
    return await handler.list_all(query)


@router.get("/{borrower_id}", response_model=BorrowerResponseSchema)
async def get_borrower(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> Borrower:
    """Fetch borrower profile details by ID."""
    query = GetBorrowerQuery(borrower_id=borrower_id)
    handler = BorrowerQueryHandler(session)
    return await handler.get_by_id(query)
