"""
Tests for Executive Credit Memorandum generation and endpoint null-safety.
"""
import pytest
from ai.agents.reporting_agent import ReportingAgent


class TestCreditMemoGeneration:

    def test_generate_credit_memo_full_data(self):
        """Test memo generation with complete borrower financial and risk signals."""
        agent = ReportingAgent()
        borrower = {
            "id": "b-123",
            "company_name": "Acme Corp",
            "sector": "Manufacturing",
            "country": "USA",
            "updated_at": "2026-09-01T00:00:00Z",
        }
        health = {"score": 85.5, "category": "LOW RISK"}
        default_pred = {
            "default_probability": 3.2,
            "risk_category": "LOW",
            "z_score": 3.8,
            "risk_factors": ["Stable margins", "Low leverage"],
        }
        covenants = [
            {
                "id": "c-1",
                "covenant_name": "Maximum Leverage Ratio",
                "covenant_type": "maintenance",
                "status": "healthy",
                "current_value": 2.1,
                "threshold_value": 4.0,
                "headroom_pct": 47.5,
                "reason": "Well below 4.0x threshold",
            }
        ]
        financials = {
            "revenue": 2500000000.0,
            "ebitda": 450000000.0,
            "net_income": 210000000.0,
            "total_debt": 900000000.0,
            "cash": 300000000.0,
            "leverage_ratio": 2.0,
            "interest_coverage": 5.5,
            "currency": "USD",
        }
        loans = [
            {
                "id": "l-1",
                "loan_type": "Term Loan B",
                "principal_amount": 50000000.0,
                "currency": "USD",
                "interest_rate": 6.5,
                "maturity_date": "2030-01-01",
                "status": "active",
            }
        ]

        memo = agent.generate_credit_memo(
            borrower=borrower,
            health=health,
            default_pred=default_pred,
            covenants=covenants,
            financials=financials,
            loans=loans,
        )

        assert memo["title"] == "Executive Credit Memorandum — Acme Corp"
        assert memo["borrower"]["company_name"] == "Acme Corp"
        assert memo["summary"]["health_score"] == 85.5
        assert memo["summary"]["default_probability"] == 3.2
        assert memo["summary"]["recommendation"] == "APPROVE / MAINTAIN CREDIT FACILITY"
        assert memo["financial_highlights"]["revenue"] == 2500000000.0
        assert len(memo["facilities"]) == 1
        assert len(memo["evidence_sources"]) == 3

    def test_generate_credit_memo_missing_data_null_safe(self):
        """Test memo generation with empty/missing metrics renders gracefully without errors."""
        agent = ReportingAgent()
        borrower = {
            "id": "b-456",
            "company_name": "New Borrower Inc",
            "sector": "Technology",
            "country": "USA",
        }
        health = {"score": None, "category": "UNANALYZED"}
        default_pred = {
            "default_probability": None,
            "risk_category": "UNANALYZED",
            "z_score": None,
            "risk_factors": [],
        }

        memo = agent.generate_credit_memo(
            borrower=borrower,
            health=health,
            default_pred=default_pred,
            covenants=[],
            financials={},
            loans=[],
            stress=None,
        )

        assert memo["title"] == "Executive Credit Memorandum — New Borrower Inc"
        assert memo["summary"]["health_score"] is None
        assert memo["summary"]["default_probability"] is None
        assert memo["summary"]["recommendation"] == "PENDING ANALYSIS / INSUFFICIENT DATA"
        assert memo["financial_highlights"]["revenue"] is None
        assert memo["covenant_summary"]["total_monitored"] == 0
        assert memo["facilities"] == []
