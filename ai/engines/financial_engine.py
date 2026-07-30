"""
Financial Analysis Engine — Sprint 3.
Computes all derived financial ratios from raw extracted metrics
and persists extended calculations back to the database.
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

logger = structlog.get_logger(__name__)


class FinancialMetrics:
    """Computed financial metrics for a single reporting period."""

    def __init__(self, raw: dict):
        self.agreement_id: str = raw.get("agreement_id", "")
        self.borrower_id: str = raw.get("borrower_id", "")
        self.reporting_period: str = raw.get("reporting_period", "")

        # Raw figures (convert Decimal → float for calculation)
        self.revenue: float = float(raw.get("revenue") or 0)
        self.ebitda: float = float(raw.get("ebitda") or 0)
        self.net_income: float = float(raw.get("net_income") or 0)
        self.total_debt: float = float(raw.get("total_debt") or 0)
        self.cash: float = float(raw.get("cash") or 0)
        self.interest_expense: float = float(raw.get("interest_expense") or 0)

        # Calculated ratios
        self.net_debt: float = self._calc_net_debt()
        self.leverage_ratio: float = self._calc_leverage()
        self.interest_coverage: float = self._calc_interest_coverage()
        self.dscr: float = self._calc_dscr()
        self.current_ratio: float = float(raw.get("current_ratio") or 0)
        self.quick_ratio: float = float(raw.get("quick_ratio") or 0)
        self.debt_to_equity: float = self._calc_debt_to_equity()
        self.free_cash_flow: float = self._calc_fcf()

    # ── Private calculation methods ────────────────────────────────────────────

    def _calc_net_debt(self) -> float:
        """Net Debt = Total Debt - Cash"""
        return self.total_debt - self.cash

    def _calc_leverage(self) -> float:
        """Leverage Ratio = Net Debt / EBITDA"""
        if self.ebitda == 0:
            return 0.0
        return round(self._calc_net_debt() / self.ebitda, 2)

    def _calc_interest_coverage(self) -> float:
        """Interest Coverage = EBITDA / Interest Expense"""
        if self.interest_expense == 0:
            return 0.0
        return round(self.ebitda / self.interest_expense, 2)

    def _calc_dscr(self) -> float:
        """
        DSCR = EBITDA / Total Debt Service (approximated as interest expense * 1.5
        when principal payments aren't available)
        """
        debt_service = self.interest_expense * 1.5 if self.interest_expense > 0 else 1
        if debt_service == 0:
            return 0.0
        return round(self.ebitda / debt_service, 2)

    def _calc_debt_to_equity(self) -> float:
        """
        Debt-to-Equity proxy using net income as equity proxy.
        In the absence of balance sheet equity, use Net Income * 8 (P/E ~8x)
        """
        equity_proxy = self.net_income * 8 if self.net_income > 0 else 1
        if equity_proxy == 0:
            return 0.0
        return round(self.total_debt / equity_proxy, 2)

    def _calc_fcf(self) -> float:
        """Free Cash Flow = EBITDA - CapEx proxy (10% of revenue)"""
        capex_proxy = self.revenue * 0.10
        return round(self.ebitda - capex_proxy, 2)

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

        # Persist computed fields back to the row
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
                "leverage_ratio": metrics.leverage_ratio,
                "interest_coverage": metrics.interest_coverage,
                "dscr": metrics.dscr,
                "debt_to_equity": metrics.debt_to_equity,
                "free_cash_flow": metrics.free_cash_flow,
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
        )
        return metrics
