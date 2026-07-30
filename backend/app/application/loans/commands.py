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
    agreement_id: str
    amount: Decimal
    currency: str
    interest_rate: float
    start_date: date
    maturity_date: date
    status: LoanStatus = LoanStatus.ACTIVE
