"""
Borrower API schemas.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.domain.value_objects.risk_rating import RiskLevel


class RiskRatingSchema(BaseModel):
    level: RiskLevel
    score: int = Field(..., ge=1, le=10)


class BorrowerCreateSchema(BaseModel):
    organization_id: str
    company_name: str = Field(..., min_length=2, max_length=100)
    sector: str = Field(..., min_length=2, max_length=100)
    country: str = Field(..., min_length=2, max_length=100)
    risk_rating: RiskRatingSchema


class BorrowerResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    company_name: str
    sector: str
    country: str
    risk_rating: RiskRatingSchema
    is_archived: bool = False
    archived_at: datetime | None = None
    archived_by: str | None = None
