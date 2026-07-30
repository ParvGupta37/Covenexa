"""
Borrower API schemas.
"""
from pydantic import BaseModel, Field
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
    id: str
    organization_id: str
    company_name: str
    sector: str
    country: str
    risk_rating: RiskRatingSchema

    class Config:
        from_attributes = True
