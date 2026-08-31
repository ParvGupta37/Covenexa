"""
Borrower query models.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class GetBorrowerQuery:
    borrower_id: str


@dataclass
class ListBorrowersQuery:
    organization_id: Optional[str] = None
    status: str = "ACTIVE"
