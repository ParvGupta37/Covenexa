"""
Borrower application commands.
"""
from dataclasses import dataclass
from app.domain.value_objects.risk_rating import RiskLevel


@dataclass
class CreateBorrowerCommand:
    organization_id: str
    company_name: str
    sector: str
    country: str
    risk_level: RiskLevel
    risk_score: int


@dataclass
class ArchiveBorrowerCommand:
    borrower_id: str
    organization_id: str
    user_id: str


@dataclass
class RestoreBorrowerCommand:
    borrower_id: str
    organization_id: str


@dataclass
class DeleteBorrowerCommand:
    borrower_id: str
    organization_id: str
