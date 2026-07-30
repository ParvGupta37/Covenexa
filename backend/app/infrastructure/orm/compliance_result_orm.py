"""
SQLAlchemy ORM model for Compliance Results.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.compliance_result import ComplianceResult, ComplianceStatus
from app.infrastructure.orm.base import Base


class ComplianceResultORM(Base):
    __tablename__ = "compliance_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False
    )
    covenant_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=ComplianceStatus.COMPLIANT.value)
    headroom: Mapped[float] = mapped_column(Float, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_entity(self) -> ComplianceResult:
        return ComplianceResult(
            id=self.id,
            borrower_id=self.borrower_id,
            covenant_id=self.covenant_id,
            status=ComplianceStatus(self.status),
            headroom=self.headroom,
            checked_at=self.checked_at,
        )

    @classmethod
    def from_entity(cls, entity: ComplianceResult) -> "ComplianceResultORM":
        return cls(
            id=entity.id,
            borrower_id=entity.borrower_id,
            covenant_id=entity.covenant_id,
            status=entity.status.value,
            headroom=entity.headroom,
            checked_at=entity.checked_at,
        )
