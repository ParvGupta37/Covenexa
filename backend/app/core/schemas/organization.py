"""
Organization API schemas.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class OrganizationCreateSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    industry: str = Field(..., min_length=2, max_length=100)


class OrganizationResponseSchema(BaseModel):
    id: str
    name: str
    industry: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationStatsSchema(BaseModel):
    borrower_count: int
    loan_count: int
    agreement_count: int


class OrganizationDetailSchema(BaseModel):
    id: str
    name: str
    industry: str
    created_at: datetime
    stats: OrganizationStatsSchema

    class Config:
        from_attributes = True
