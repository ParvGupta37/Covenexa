"""
SQLAlchemy ORM model for Reports.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.report import Report, ReportType
from app.infrastructure.orm.base import Base


class ReportORM(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False
    )
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_path: Mapped[str] = mapped_column(String(500), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_entity(self) -> Report:
        return Report(
            id=self.id,
            borrower_id=self.borrower_id,
            report_type=ReportType(self.report_type),
            report_path=self.report_path,
            generated_at=self.generated_at,
        )

    @classmethod
    def from_entity(cls, entity: Report) -> "ReportORM":
        return cls(
            id=entity.id,
            borrower_id=entity.borrower_id,
            report_type=entity.report_type.value,
            report_path=entity.report_path,
            generated_at=entity.generated_at,
        )
