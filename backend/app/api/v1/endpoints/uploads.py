"""
Document Upload & SEC EDGAR Ingestion endpoints.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.uploads.commands import UploadDocumentCommand
from app.application.uploads.handlers import UploadDocumentHandler
from app.core.dependencies import get_db_session, require_role
from app.core.schemas.upload import UploadResponseSchema
from app.domain.entities.user import UserRole
from integrations.sec.pipeline import SECDocumentPipeline

router = APIRouter(prefix="/uploads", tags=["Uploads"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


class SECUploadRequest(BaseModel):
    loan_id: str
    sec_url: str
    document_type: str = "sec_10k"


@router.post(
    "/",
    response_model=UploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def upload_document(
    request: Request,
    loan_id: str = Form(...),
    file_type: str = Form("loan_agreement"),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Ingest a PDF, DOCX, XLSX, or CSV file associated with a loan."""
    file.file.seek(0, 2)
    size_bytes = file.file.tell()
    file.file.seek(0)

    command = UploadDocumentCommand(
        loan_id=loan_id,
        file_name=file.filename,
        file_type=file_type,
        content=file.file,
        size_bytes=size_bytes,
    )
    event_bus = getattr(request.app.state, "event_bus", None)
    handler = UploadDocumentHandler(session, event_bus=event_bus)
    agreement = await handler.handle(command)

    return {
        "agreement_id": agreement.id,
        "loan_id": agreement.loan_id,
        "file_name": file.filename,
        "file_path": agreement.file_path,
        "file_type": file_type,
        "upload_date": agreement.upload_date,
        "status": "uploaded",
    }


@router.post(
    "/sec-url",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def ingest_sec_url(
    req: SECUploadRequest,
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Ingest an SEC EDGAR filing directly via its EDGAR URL."""
    pipeline = SECDocumentPipeline()
    try:
        res = await pipeline.process_sec_url(
            session=session,
            sec_url=req.sec_url,
            loan_id=req.loan_id,
            document_type=req.document_type
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
