"""
Document Processing API Schemas — Sprint 2.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class DocumentStatusSchema(BaseModel):
    id: str = Field(..., alias="agreement_id")
    loan_id: str
    file_path: str
    document_type: str
    processing_status: str
    processing_error: Optional[str] = None
    processed_at: Optional[datetime] = None
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    upload_date: datetime

    @property
    def agreement_id(self) -> str:
        return self.id

    model_config = {"populate_by_name": True, "from_attributes": True}


class ChunkSchema(BaseModel):
    id: str
    agreement_id: str
    chunk_index: int
    page_number: Optional[int] = None
    section: Optional[str] = None
    content: str
    char_count: int
    embedding_id: Optional[str] = None
    created_at: datetime


class CovenantSchema(BaseModel):
    id: str
    agreement_id: str
    borrower_id: str
    name: str
    covenant_type: str
    formula: Optional[str] = None
    threshold: Optional[float] = None
    threshold_direction: Optional[str] = None
    frequency: Optional[str] = None
    cure_period_days: Optional[int] = None
    is_event_of_default: bool
    amendment_references: Optional[str] = None
    raw_text: Optional[str] = None
    extracted_at: datetime


class FinancialMetricSchema(BaseModel):
    id: str
    agreement_id: str
    borrower_id: str
    reporting_period: Optional[str] = None
    revenue: Optional[Decimal] = None
    ebitda: Optional[Decimal] = None
    net_income: Optional[Decimal] = None
    total_debt: Optional[Decimal] = None
    cash: Optional[Decimal] = None
    interest_expense: Optional[Decimal] = None
    leverage_ratio: Optional[float] = None
    interest_coverage: Optional[float] = None
    currency: str = "USD"
    extracted_at: datetime
