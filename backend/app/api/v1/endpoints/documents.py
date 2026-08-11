"""
Document Processing endpoints — Sprint 2.
Provides status, chunks, covenants, and financial metrics for ingested agreements.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role
from app.core.schemas.document import (
    ChunkSchema,
    CovenantSchema,
    DocumentStatusSchema,
    FinancialMetricSchema,
)
from app.domain.entities.user import UserRole

router = APIRouter(prefix="/documents", tags=["Documents"])

_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


def _map_agreement(r: dict) -> dict:
    d = dict(r)
    d["agreement_id"] = d.get("id", "")
    return d


# ── GET /documents/loan/{loan_id} (Must come BEFORE /{agreement_id}) ──────────
@router.get(
    "/loan/{loan_id}",
    response_model=List[DocumentStatusSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_documents_for_loan(
    loan_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> List[DocumentStatusSchema]:
    """List all agreements/documents uploaded for a specific loan with pagination."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    result = await session.execute(
        text("SELECT * FROM agreements WHERE loan_id = :loan_id ORDER BY upload_date DESC LIMIT :limit OFFSET :offset"),
        {"loan_id": loan_id, "limit": limit, "offset": offset},
    )
    rows = result.mappings().all()
    return [DocumentStatusSchema(**_map_agreement(r)) for r in rows]


# ── GET /documents/borrower/{borrower_id} ──────────────────────────────────────
@router.get(
    "/borrower/{borrower_id}",
    response_model=List[DocumentStatusSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_documents_for_borrower(
    borrower_id: str,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> List[DocumentStatusSchema]:
    """List all agreements/documents uploaded for a borrower across all facilities with pagination."""
    limit = max(1, min(500, limit))
    offset = max(0, offset)
    result = await session.execute(
        text("""
            SELECT a.* 
            FROM agreements a
            JOIN loans l ON a.loan_id = l.id
            WHERE l.borrower_id = :borrower_id
            ORDER BY a.upload_date DESC
            LIMIT :limit OFFSET :offset
        """),
        {"borrower_id": borrower_id, "limit": limit, "offset": offset},
    )
    rows = result.mappings().all()
    return [DocumentStatusSchema(**_map_agreement(r)) for r in rows]


# ── GET /documents/{agreement_id} ──────────────────────────────────────────────
@router.get(
    "/{agreement_id}",
    response_model=DocumentStatusSchema,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_document_status(
    agreement_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> DocumentStatusSchema:
    """Return processing status and metadata for an agreement."""
    result = await session.execute(
        text("SELECT * FROM agreements WHERE id = :id"),
        {"id": agreement_id},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agreement not found.")
    return DocumentStatusSchema(**_map_agreement(row))


# ── GET /documents/{agreement_id}/chunks ───────────────────────────────────────
@router.get(
    "/{agreement_id}/chunks",
    response_model=List[ChunkSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_document_chunks(
    agreement_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> List[ChunkSchema]:
    """Return all semantic text chunks for an agreement."""
    result = await session.execute(
        text("""
            SELECT * FROM document_chunks
            WHERE agreement_id = :agreement_id
            ORDER BY chunk_index
        """),
        {"agreement_id": agreement_id},
    )
    rows = result.mappings().all()
    return [ChunkSchema(**dict(r)) for r in rows]


# ── GET /documents/{agreement_id}/covenants ────────────────────────────────────
@router.get(
    "/{agreement_id}/covenants",
    response_model=List[CovenantSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_document_covenants(
    agreement_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> List[CovenantSchema]:
    """Return all AI-extracted covenants for an agreement."""
    result = await session.execute(
        text("""
            SELECT * FROM covenants
            WHERE agreement_id = :agreement_id
            ORDER BY extracted_at
        """),
        {"agreement_id": agreement_id},
    )
    rows = result.mappings().all()
    return [CovenantSchema(**dict(r)) for r in rows]


# ── GET /documents/{agreement_id}/financials ───────────────────────────────────
@router.get(
    "/{agreement_id}/financials",
    response_model=List[FinancialMetricSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_document_financials(
    agreement_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> List[FinancialMetricSchema]:
    """Return all AI-extracted financial metrics for an agreement."""
    result = await session.execute(
        text("""
            SELECT * FROM financial_metrics
            WHERE agreement_id = :agreement_id
            ORDER BY extracted_at DESC
        """),
        {"agreement_id": agreement_id},
    )
    rows = result.mappings().all()
    return [FinancialMetricSchema(**dict(r)) for r in rows]
