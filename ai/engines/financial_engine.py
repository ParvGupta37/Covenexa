"""
Financial Analysis Engine — Sprint 3 (Phase 2B: HIGH-3 fix).

RULE: None = incalculable / unavailable. 0.0 = legitimate calculated zero.
- All derived ratio methods return Optional[float].
- A zero denominator yields None (undefined ratio), NOT 0.0.
- Raw input fallback from DB None → 0.0 is kept ONLY for balance-sheet
  items (revenue, debt, cash) where None and zero are financially
  equivalent in context. For EBITDA and interest_expense the distinction
  matters and those remain None-propagating.
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

logger = structlog.get_logger(__name__)

# Maximum sensible interest-coverage multiple before the ratio is
# considered unreliable (near-zero interest expense artefact).
MAX_COVERAGE_CAP = 50.0


class FinancialMetrics:
    """Computed financial metrics for a single reporting period."""

    def __init__(self, raw: dict):
        self.agreement_id: str = raw.get("agreement_id", "")
        self.borrower_id: str = raw.get("borrower_id", "")
        self.reporting_period: str = raw.get("reporting_period", "")

        # ── Raw extracted figures (None preserved for missing fields) ──────
        # Balance-sheet items: None → 0 is acceptable (missing = zero balance)
        self.revenue: float = float(raw["revenue"]) if raw.get("revenue") is not None else 0.0
        self.net_income: float = float(raw["net_income"]) if raw.get("net_income") is not None else 0.0
        self.total_debt: float = float(raw["total_debt"]) if raw.get("total_debt") is not None else 0.0
        self.cash: float = float(raw["cash"]) if raw.get("cash") is not None else 0.0
        self.current_ratio: float = float(raw["current_ratio"]) if raw.get("current_ratio") is not None else 0.0
        self.quick_ratio: float = float(raw["quick_ratio"]) if raw.get("quick_ratio") is not None else 0.0

        # Denominator-sensitive items: None is preserved → incalculable ratio.
        # A stored DB value of 0.0 means "actually zero"; None means "not reported".
        self.ebitda: Optional[float] = float(raw["ebitda"]) if raw.get("ebitda") is not None else None
        self.interest_expense: Optional[float] = (
            float(raw["interest_expense"]) if raw.get("interest_expense") is not None else None
        )

        # ── Derived ratios (all Optional — None means incalculable) ───────
        self.net_debt: float = self._calc_net_debt()
        self.leverage_ratio: Optional[float] = self._calc_leverage()
        self.interest_coverage: Optional[float] = self._calc_interest_coverage()
        self.dscr: Optional[float] = self._calc_dscr()
        self.debt_to_equity: Optional[float] = self._calc_debt_to_equity()
        self.free_cash_flow: Optional[float] = self._calc_fcf()

        # ── Data-quality summary ────────────────────────────────────────────
        self.data_quality = self._assess_data_quality()

    # ── Private calculation methods ──────────────────────────────────────────

    def _calc_net_debt(self) -> float:
        """Net Debt = Total Debt − Cash (always calculable; zero is valid)."""
        return self.total_debt - self.cash

    def _calc_leverage(self) -> Optional[float]:
        """Leverage Ratio = Net Debt / EBITDA.
        Returns None when EBITDA is missing or zero (undefined ratio).
        """
        if self.ebitda is None:
            return None
        if self.ebitda == 0.0:
            # Zero EBITDA with any debt is a distress signal, not a clean ratio.
            return None
        return round(self._calc_net_debt() / self.ebitda, 2)

    def _calc_interest_coverage(self) -> Optional[float]:
        """Interest Coverage = EBITDA / Interest Expense.
        Returns None when interest_expense is missing or zero.
        Zero interest ≠ zero coverage; it means the ratio is undefined.
        """
        if self.ebitda is None:
            return None
        if self.interest_expense is None or self.interest_expense == 0.0:
            # Near-zero interest: ratio is undefined (not "zero coverage").
            return None
        raw_coverage = self.ebitda / self.interest_expense
        # Cap to MAX_COVERAGE_CAP to prevent formula domination from
        # near-zero interest-expense artefacts (e.g. SEC unit mismatch).
        if raw_coverage > MAX_COVERAGE_CAP:
            logger.warning(
                "financial_engine.coverage_capped",
                raw=raw_coverage,
                cap=MAX_COVERAGE_CAP,
                borrower_id=self.borrower_id,
            )
            return float(MAX_COVERAGE_CAP)
        return round(raw_coverage, 2)

    def _calc_dscr(self) -> Optional[float]:
        """DSCR = EBITDA / Debt Service (approx interest_expense × 1.5).
        Returns None if EBITDA or interest_expense is missing/zero.
        Do NOT use hardcoded debt_service=1; that produces meaningless ratios.
        """
        if self.ebitda is None or self.interest_expense is None:
            return None
        if self.interest_expense == 0.0:
            return None
        debt_service = self.interest_expense * 1.5
        return round(self.ebitda / debt_service, 2)

    def _calc_debt_to_equity(self) -> Optional[float]:
        """Debt-to-Equity proxy using net_income * 8 as equity approximation.
        Returns None when net_income ≤ 0 (no valid equity proxy available).
        Do NOT use equity_proxy=1; that produces a dimensionless nonsense value.
        """
        if self.net_income <= 0:
            return None
        equity_proxy = self.net_income * 8
        return round(self.total_debt / equity_proxy, 2)

    def _calc_fcf(self) -> Optional[float]:
        """Free Cash Flow = EBITDA − CapEx proxy (10% of revenue).
        Returns None if EBITDA is unavailable.
        """
        if self.ebitda is None:
            return None
        capex_proxy = self.revenue * 0.10
        return round(self.ebitda - capex_proxy, 2)

    def _assess_data_quality(self) -> dict:
        """Summarise which inputs and ratios are available vs. missing."""
        return {
            "ebitda_available": self.ebitda is not None,
            "interest_expense_available": self.interest_expense is not None and self.interest_expense > 0,
            "revenue_available": self.revenue > 0,
            "debt_available": self.total_debt > 0,
            "leverage_calculable": self.leverage_ratio is not None,
            "coverage_calculable": self.interest_coverage is not None,
            "dscr_calculable": self.dscr is not None,
        }

    def to_summary(self) -> dict:
        return {
            "revenue": self.revenue,
            "ebitda": self.ebitda,
            "net_income": self.net_income,
            "total_debt": self.total_debt,
            "cash": self.cash,
            "net_debt": self.net_debt,
            "interest_expense": self.interest_expense,
            "leverage_ratio": self.leverage_ratio,
            "interest_coverage": self.interest_coverage,
            "dscr": self.dscr,
            "debt_to_equity": self.debt_to_equity,
            "free_cash_flow": self.free_cash_flow,
            "data_quality": self.data_quality,
        }


class FinancialEngine:
    """
    Computes all financial ratios for a borrower and persists updates
    to the financial_metrics table.
    """

    async def compute_and_persist(self, session, borrower_id: str) -> Optional[FinancialMetrics]:
        """
        Loads the latest raw financial_metrics row for the borrower,
        computes all ratios, and updates the DB record.
        Returns the computed FinancialMetrics object, or None if no data.
        """
        from sqlalchemy import text

        result = await session.execute(
            text("""
                SELECT * FROM financial_metrics
                WHERE borrower_id = :borrower_id
                ORDER BY extracted_at DESC
                LIMIT 1
            """),
            {"borrower_id": borrower_id},
        )
        row = result.mappings().first()
        if not row:
            logger.info("financial_engine.no_metrics", borrower_id=borrower_id)
            return None

        metrics = FinancialMetrics(dict(row))

        # Persist computed fields back — None is stored as SQL NULL (not 0).
        await session.execute(
            text("""
                UPDATE financial_metrics SET
                    net_debt          = :net_debt,
                    leverage_ratio    = :leverage_ratio,
                    interest_coverage = :interest_coverage,
                    dscr              = :dscr,
                    debt_to_equity    = :debt_to_equity,
                    free_cash_flow    = :free_cash_flow
                WHERE id = :id
            """),
            {
                "net_debt": metrics.net_debt,
                "leverage_ratio": metrics.leverage_ratio,      # may be NULL
                "interest_coverage": metrics.interest_coverage,  # may be NULL
                "dscr": metrics.dscr,                          # may be NULL
                "debt_to_equity": metrics.debt_to_equity,      # may be NULL
                "free_cash_flow": metrics.free_cash_flow,      # may be NULL
                "id": row["id"],
            },
        )
        await session.commit()
        logger.info(
            "financial_engine.computed",
            borrower_id=borrower_id,
            leverage=metrics.leverage_ratio,
            coverage=metrics.interest_coverage,
            dscr=metrics.dscr,
            data_quality=metrics.data_quality,
        )
        return metrics
