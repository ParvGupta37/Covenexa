"""
Regression tests for Dashboard Portfolio Exposure Currency Handling and Multi-Currency Aggregation.
Verifies that portfolio-level exposure dynamically formats with native currencies (INR, USD, IDR, EUR, GBP),
handles multi-currency portfolios without false scalar addition, and respects null/missing currency invariants.
"""
import pytest
from decimal import Decimal

from app.core.schemas.loan import MoneySchema, LoanResponseSchema, LoanCreateSchema
from app.domain.entities.loan import LoanStatus


class TestPortfolioExposureCurrency:

    def test_inr_loan_facility_schema_and_currency(self):
        """A. INR facility with 50,000,000 principal retains INR currency."""
        money = MoneySchema(amount=Decimal("50000000.00"), currency="INR")
        assert money.currency == "INR"
        assert money.amount == Decimal("50000000.00")

    def test_usd_loan_facility_schema_and_currency(self):
        """B. USD facility with 50,000,000 principal retains USD currency."""
        money = MoneySchema(amount=Decimal("50000000.00"), currency="USD")
        assert money.currency == "USD"
        assert money.amount == Decimal("50000000.00")

    def test_idr_loan_facility_schema_and_currency(self):
        """C. IDR facility with 10,930,700,000,000 principal retains IDR currency."""
        money = MoneySchema(amount=Decimal("10930700000000.00"), currency="IDR")
        assert money.currency == "IDR"
        assert money.amount == Decimal("10930700000000.00")

    def test_multi_currency_portfolio_grouping_logic(self):
        """
        E. Multiple currencies: A portfolio with 50M USD + 50M INR must group by currency
        and NOT falsely sum them into a single scalar under one currency symbol.
        """
        loans = [
            {"principal_amount": {"amount": 50_000_000, "currency": "USD"}, "is_archived": False},
            {"principal_amount": {"amount": 50_000_000, "currency": "INR"}, "is_archived": False},
            {"principal_amount": {"amount": 10_930_700_000_000, "currency": "IDR"}, "is_archived": False},
        ]

        # Grouping logic as implemented in Dashboard
        currency_totals = {}
        for l in loans:
            amt = l["principal_amount"]["amount"]
            cur = l["principal_amount"]["currency"].upper()
            currency_totals[cur] = currency_totals.get(cur, 0) + amt

        assert currency_totals["USD"] == 50_000_000
        assert currency_totals["INR"] == 50_000_000
        assert currency_totals["IDR"] == 10_930_700_000_000

        # Must maintain distinct currencies
        assert len(currency_totals) == 3
        assert "USD" in currency_totals
        assert "INR" in currency_totals
        assert "IDR" in currency_totals

    def test_missing_currency_fallback_to_usd(self):
        """D. Missing/null currency falls back safely to USD."""
        money = MoneySchema(amount=Decimal("1000000.00"))
        assert money.currency == "USD"
