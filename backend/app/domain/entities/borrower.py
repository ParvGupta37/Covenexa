"""
Borrower domain entity.
"""
from dataclasses import dataclass
from datetime import datetime
from app.domain.value_objects.risk_rating import RiskRating


@dataclass
class Borrower:
    id: str
    organization_id: str
    company_name: str
    sector: str
    country: str
    risk_rating: RiskRating
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by: str | None = None

    def update_risk_rating(self, new_rating: RiskRating) -> None:
        self.risk_rating = new_rating

    def archive(self, user_id: str, archived_at: datetime | None = None) -> None:
        self.is_archived = True
        self.archived_at = archived_at
        self.archived_by = user_id

    def restore(self) -> None:
        self.is_archived = False
        self.archived_at = None
        self.archived_by = None
