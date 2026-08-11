"""
Loan application commands.
"""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from app.domain.entities.loan import LoanStatus


@dataclass
class CreateLoanCommand:
    borrower_id: str
    amount: Decimal
    currency: str
    interest_rate: float
    start_date: date
    maturity_date: date
    agreement_id: str | None = None
    status: LoanStatus = LoanStatus.ACTIVE
