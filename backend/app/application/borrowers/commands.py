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
