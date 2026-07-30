"""
Document Upload endpoints.
"""
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.uploads.commands import UploadDocumentCommand
from app.application.uploads.handlers import UploadDocumentHandler
from app.core.dependencies import get_db_session, require_role
from app.core.schemas.upload import UploadResponseSchema
from app.domain.entities.user import UserRole

router = APIRouter(prefix="/uploads", tags=["Uploads"])


@router.post(
    "/",
    response_model=UploadResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]))],
)
async def upload_document(
    request: Request,
    loan_id: str = Form(...),
    file_type: str = Form("loan_agreement"),  # e.g., 'loan_agreement', 'amendment'
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Ingest a PDF or document file associated with a loan.
    Validates file properties, saves to disk, logs in PostgreSQL, and publishes an event to Redis.
    """
    # Size check can be read from file stream descriptor
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
