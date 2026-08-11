"""
SQLAlchemy ORM model for Loans.
"""
from datetime import date
from decimal import Decimal
import uuid

from sqlalchemy import Date, Float, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.loan import Loan, LoanStatus
from app.domain.value_objects.money import Money
from app.infrastructure.orm.base import Base


class LoanORM(Base):
    __tablename__ = "loans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    borrower_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False
    )
    agreement_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("agreements.id", ondelete="SET NULL"), nullable=True
    )
    
    # Store principal amount money fields
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    interest_rate: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    maturity_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=LoanStatus.ACTIVE.value)

    def to_entity(self) -> Loan:
        return Loan(
            id=self.id,
            borrower_id=self.borrower_id,
            agreement_id=self.agreement_id,
            principal_amount=Money(amount=self.principal_amount, currency=self.currency),
            interest_rate=self.interest_rate,
            start_date=self.start_date,
            maturity_date=self.maturity_date,
            status=LoanStatus(self.status),
        )

    @classmethod
    def from_entity(cls, entity: Loan) -> "LoanORM":
        return cls(
            id=entity.id,
            borrower_id=entity.borrower_id,
            agreement_id=entity.agreement_id,
            principal_amount=entity.principal_amount.amount,
            currency=entity.principal_amount.currency,
            interest_rate=entity.interest_rate,
            start_date=entity.start_date,
            maturity_date=entity.maturity_date,
            status=entity.status.value,
        )
