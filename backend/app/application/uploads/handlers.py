"""
Document Upload application command handlers.
Saves files to storage, registers them in SQL, and triggers the Event Bus.
"""
import os
import uuid
from datetime import datetime, timezone
from typing import Any
import aiofiles
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.uploads.commands import UploadDocumentCommand
from app.core.config import settings
from app.core.exceptions import DomainException, EntityNotFoundException
from app.infrastructure.orm.agreement_orm import AgreementORM
from app.infrastructure.repositories.loan_repository_impl import LoanRepositoryImpl
from event_bus.events.document_events import DocumentUploadedEvent
from event_bus.redis_event_bus import RedisEventBus
from integrations.redis.client import RedisClient

logger = structlog.get_logger(__name__)


class UploadDocumentHandler:
    def __init__(self, session: AsyncSession, event_bus: Any = None) -> None:
        self._session = session
        self._loan_repo = LoanRepositoryImpl(session)
        self._event_bus = event_bus

    async def handle(self, command: UploadDocumentCommand) -> AgreementORM:
        # Verify loan exists and is active
        loan = await self._loan_repo.get_by_id(command.loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", command.loan_id)

        if getattr(loan, "is_archived", False) is True:
            raise DomainException("Cannot upload documents to an archived loan facility. Restore the facility first.")

        # Validate file extension
        ext = command.file_name.split(".")[-1].lower()
        if ext not in settings.allowed_extensions_list:
            raise DomainException(f"Unsupported file extension: .{ext}")

        # Validate file size
        max_bytes = settings.UPLOAD_MAX_SIZE_MB * 1024 * 1024
        if command.size_bytes > max_bytes:
            raise DomainException(f"File size exceeds maximum limit of {settings.UPLOAD_MAX_SIZE_MB}MB.")

        # Create unique, path-sanitized filename to prevent overwrites & path traversal
        unique_id = str(uuid.uuid4())
        clean_filename = os.path.basename(command.file_name) if command.file_name else "file.pdf"
        safe_filename = f"{unique_id}_{clean_filename}"
        
        # Ensure upload folder exists
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        # Save to local disk uploads volume
        logger.info("upload.saving_file", file_path=file_path)
        async with aiofiles.open(file_path, "wb") as out_file:
            # Read and write chunks
            content = command.content.read()
            await out_file.write(content)

        # Register Agreement in database
        agreement_orm = AgreementORM(
            id=unique_id,
            loan_id=command.loan_id,
            version="1.0",
            file_path=file_path,
            document_type=command.file_type,
            upload_date=datetime.now(timezone.utc),
        )
        self._session.add(agreement_orm)
        await self._session.flush()
        from sqlalchemy import text
        await self._session.execute(
            text("UPDATE loans SET agreement_id = :aid WHERE id = :lid"),
            {"aid": agreement_orm.id, "lid": command.loan_id}
        )
        await self._session.commit()

        # Emit DocumentUploadedEvent to Event Bus (Redis or direct handler)
        event_data = {
            "borrower_id": loan.borrower_id,
            "agreement_id": agreement_orm.id,
            "file_path": file_path,
            "file_type": command.file_type,
        }
        
        if self._event_bus:
            try:
                event = DocumentUploadedEvent(**event_data)
                await self._event_bus.publish(event)
                logger.info("upload.event_emitted", agreement_id=agreement_orm.id)
            except Exception as exc:
                logger.error("upload.event_publish_failed", error=str(exc))
        else:
            try:
                from event_bus.handlers.document_handler import DocumentUploadedHandler as DocHandler
                await DocHandler().handle(event_data)
                logger.info("upload.direct_handler_triggered", agreement_id=agreement_orm.id)
            except Exception as exc:
                logger.error("upload.direct_handler_failed", error=str(exc))

        return agreement_orm

class SimpleMockUploadHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._loan_repo = LoanRepositoryImpl(session)

    async def handle_simple(self, loan_id: str, file_name: str, file_type: str, file_path: str) -> AgreementORM:
        loan = await self._loan_repo.get_by_id(loan_id)
        if not loan:
            raise EntityNotFoundException("Loan", loan_id)
        agreement_orm = AgreementORM(
            id=str(uuid.uuid4()),
            loan_id=loan_id,
            version="1.0",
            file_path=file_path,
            upload_date=datetime.now(timezone.utc),
        )
        self._session.add(agreement_orm)
        await self._session.flush()
        return agreement_orm
