"""
SQLAlchemy ORM model for Financial Metrics.
Stores AI-extracted financial metrics from uploaded financial statements and agreements.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from decimal import Decimal

from app.infrastructure.orm.base import Base


class FinancialMetricORM(Base):
    __tablename__ = "financial_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agreement_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reporting_period: Mapped[str] = mapped_column(String(50), nullable=True)

    # Core financial figures (all in base currency units)
    revenue: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    ebitda: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    net_income: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    total_debt: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    cash: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)
    interest_expense: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=True)

    # Calculated ratios
    leverage_ratio: Mapped[float] = mapped_column(Float, nullable=True)   # total_debt / EBITDA
    interest_coverage: Mapped[float] = mapped_column(Float, nullable=True)  # EBITDA / interest_expense

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    extracted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
