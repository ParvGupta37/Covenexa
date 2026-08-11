"""
Loan API schemas.
"""
from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from app.domain.entities.loan import LoanStatus


class MoneySchema(BaseModel):
    amount: Decimal = Field(..., ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)


class LoanCreateSchema(BaseModel):
    borrower_id: str
    principal_amount: MoneySchema
    interest_rate: float = Field(..., ge=0.0, le=1.0)
    start_date: date
    maturity_date: date
    agreement_id: str | None = None
    status: LoanStatus = LoanStatus.ACTIVE


class LoanResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    borrower_id: str
    principal_amount: MoneySchema
    interest_rate: float
    start_date: date
    maturity_date: date
    status: LoanStatus
    agreement_id: str | None = None
