"""
Financial Events (Sprint 3 stubs).
"""
from dataclasses import dataclass
from event_bus.events.base_event import BaseEvent


@dataclass(kw_only=True)
class FinancialStatementUploadedEvent(BaseEvent):
    """
    Fired when a borrower submits new financial figures (revenue, EBITDA, etc.).
    """
    borrower_id: str
    statement_id: str
    reporting_period: str  # e.g., 'Q3_2026'

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "borrower_id": self.borrower_id,
            "statement_id": self.statement_id,
            "reporting_period": self.reporting_period,
        })
        return data
