"""
SQLAlchemy ORM model for Covenants.
Stores AI-extracted covenant clauses from loan agreements.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.orm.base import Base


class CovenantORM(Base):
    __tablename__ = "covenants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agreement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Core covenant fields
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    covenant_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="maintenance"
    )  # maintenance | incurrence | reporting | negative
    formula: Mapped[str] = mapped_column(Text, nullable=True)
    threshold: Mapped[float] = mapped_column(Float, nullable=True)
    threshold_direction: Mapped[str] = mapped_column(String(10), nullable=True)  # max | min
    frequency: Mapped[str] = mapped_column(String(50), nullable=True)  # quarterly | annual | monthly
    cure_period_days: Mapped[int] = mapped_column(Integer, nullable=True)
    is_event_of_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    amendment_references: Mapped[str] = mapped_column(Text, nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=True)  # Source chunk
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
