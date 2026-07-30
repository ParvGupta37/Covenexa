"""
Financial Statement domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from app.domain.value_objects.money import Money


@dataclass
class FinancialStatement:
    id: str
    borrower_id: str
    reporting_period: str  # e.g., 'Q1_2026'
    revenue: Money
    ebitda: Money
    total_debt: Money
    cash: Money
    uploaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def net_debt(self) -> Money:
        # Prevent negative net debt values using VO checks
        try:
            return self.total_debt - self.cash
        except ValueError:
            # If cash exceeds total debt, net debt is 0
            return Money(amount=self.cash.amount * 0, currency=self.cash.currency)
