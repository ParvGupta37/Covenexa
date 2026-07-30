"""
SQLAlchemy ORM model for Financial Statements.
"""
from datetime import datetime, timezone
from decimal import Decimal
import uuid

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.financial_statement import FinancialStatement
from app.domain.value_objects.money import Money
from app.infrastructure.orm.base import Base


class FinancialStatementORM(Base):
    __tablename__ = "financial_statements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False
    )
    reporting_period: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Financial fields storing exact numerical amounts
    revenue: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    ebitda: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    total_debt: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cash: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_entity(self) -> FinancialStatement:
        return FinancialStatement(
            id=self.id,
            borrower_id=self.borrower_id,
            reporting_period=self.reporting_period,
            revenue=Money(amount=self.revenue, currency=self.currency),
            ebitda=Money(amount=self.ebitda, currency=self.currency),
            total_debt=Money(amount=self.total_debt, currency=self.currency),
            cash=Money(amount=self.cash, currency=self.currency),
            uploaded_at=self.uploaded_at,
        )

    @classmethod
    def from_entity(cls, entity: FinancialStatement) -> "FinancialStatementORM":
        return cls(
            id=entity.id,
            borrower_id=entity.borrower_id,
            reporting_period=entity.reporting_period,
            revenue=entity.revenue.amount,
            ebitda=entity.ebitda.amount,
            total_debt=entity.total_debt.amount,
            cash=entity.cash.amount,
            currency=entity.revenue.currency,  # Assume all inputs match the same currency
            uploaded_at=entity.uploaded_at,
        )
