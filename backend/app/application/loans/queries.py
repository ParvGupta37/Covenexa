"""
Loan application queries.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetLoanQuery:
    loan_id: str


@dataclass
class ListLoansQuery:
    borrower_id: Optional[str] = None
    organization_id: Optional[str] = None
    status: str = "ACTIVE"
