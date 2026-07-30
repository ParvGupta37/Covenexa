"""
Borrower domain entity.
"""
from dataclasses import dataclass
from app.domain.value_objects.risk_rating import RiskRating


@dataclass
class Borrower:
    id: str
    organization_id: str
    company_name: str
    sector: str
    country: str
    risk_rating: RiskRating

    def update_risk_rating(self, new_rating: RiskRating) -> None:
        self.risk_rating = new_rating
