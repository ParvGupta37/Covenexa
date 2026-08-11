"""
Loan domain entity.
"""
from dataclasses import dataclass
from datetime import date
from enum import Enum
from app.domain.value_objects.money import Money


class LoanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    DEFAULTED = "DEFAULTED"


@dataclass
class Loan:
    id: str
    borrower_id: str
    principal_amount: Money
    interest_rate: float  # e.g., 0.085 for 8.5%
    start_date: date
    maturity_date: date
    status: LoanStatus
    agreement_id: str | None = None

    def __post_init__(self) -> None:
        if self.start_date >= self.maturity_date:
            raise ValueError("Start date must be before maturity date.")
        if not (0.0 <= self.interest_rate <= 1.0):
            raise ValueError("Interest rate must be between 0.0 and 1.0 (0% and 100%).")
