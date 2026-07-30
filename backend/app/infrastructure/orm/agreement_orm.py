"""
SQLAlchemy ORM model for Agreements.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.agreement import Agreement
from app.infrastructure.orm.base import Base


class AgreementORM(Base):
    __tablename__ = "agreements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    loan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("loans.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0")
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # ── Sprint 2: Processing pipeline tracking ─────────────────────────────
    document_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="loan_agreement"
    )  # loan_agreement | amendment | financial_statement
    processing_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending"
    )  # pending | parsing | chunking | embedding | extracting | done | failed
    processing_error: Mapped[str] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=True)

    def to_entity(self) -> Agreement:
        return Agreement(
            id=self.id,
            loan_id=self.loan_id,
            version=self.version,
            file_path=self.file_path,
            upload_date=self.upload_date,
        )

    @classmethod
    def from_entity(cls, entity: Agreement) -> "AgreementORM":
        return cls(
            id=entity.id,
            loan_id=entity.loan_id,
            version=entity.version,
            file_path=entity.file_path,
            upload_date=entity.upload_date,
        )
