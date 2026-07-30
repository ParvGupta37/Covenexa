"""
Compliance Events (Sprint 3 stubs).
"""
from dataclasses import dataclass
from event_bus.events.base_event import BaseEvent


@dataclass(kw_only=True)
class ComplianceCheckRequestedEvent(BaseEvent):
    """
    Fired to request compliance execution for a borrower.
    """
    borrower_id: str
    covenant_id: str
    reporting_period: str

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "borrower_id": self.borrower_id,
            "covenant_id": self.covenant_id,
            "reporting_period": self.reporting_period,
        })
        return data
