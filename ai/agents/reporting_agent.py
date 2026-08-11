"""
Reporting Agent — Sprint 4.
Generates comprehensive AI Executive Credit Memorandums and Risk Summaries
by synthesizing borrower data, financial metrics, covenant monitoring status, and default predictions.
"""
from typing import Any, Dict
import structlog

logger = structlog.get_logger(__name__)


class ReportingAgent:
    """
    Synthesizes borrower credit risk data into an Executive Credit Memorandum.
    Pure data synthesis — no LLM calls required.
    """

    @property
    def name(self) -> str:
        return "ReportingAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        borrower_data = state.get("borrower", {})
        health_data = state.get("health", {})
        default_data = state.get("default_pred", {})
        covenants = state.get("covenants", [])
        financials = state.get("financials", {})

        memo = self.generate_credit_memo(
            borrower=borrower_data,
            health=health_data,
            default_pred=default_data,
            covenants=covenants,
            financials=financials,
        )

        state["credit_memo"] = memo
        return state

    def generate_credit_memo(
        self,
        borrower: dict,
        health: dict,
        default_pred: dict,
        covenants: list,
        financials: dict,
    ) -> dict:
        company_name = borrower.get("company_name", "Borrower Entity")
        sector = borrower.get("sector", "General Industry")
        country = borrower.get("country", "USA")

        score = health.get("score")  # float or None
        category = (health.get("category") or "UNANALYZED").upper()
        def_prob = default_pred.get("default_probability")  # float or None
        risk_category = (default_pred.get("risk_category") or "UNANALYZED").upper()

        breached_covenants = [c for c in covenants if c.get("status") in ["warning", "breach", "critical"]]
        compliant_covenants = [c for c in covenants if c.get("status") == "healthy"]

        # Formulate AI Executive Opinion
        if score is None or def_prob is None:
            recommendation = "PENDING ANALYSIS / INSUFFICIENT DATA"
            recommendation_reason = (
                f"No risk intelligence pipeline analysis recorded for {company_name}. "
                "Upload a loan agreement or SEC EDGAR filing to perform automated risk evaluation."
            )
        elif score >= 80 and def_prob <= 10:
            recommendation = "APPROVE / MAINTAIN CREDIT FACILITY"
            recommendation_reason = (
                f"{company_name} maintains strong financial solvency with a high health score of {score:.1f}/100 "
                f"and low default probability ({def_prob:.1f}%). All primary debt service ratios remain comfortably within policy bounds."
            )
        elif score >= 60:
            recommendation = "CONDITIONAL APPROVAL / INCREASED MONITORING"
            recommendation_reason = (
                f"{company_name} demonstrates acceptable operational cash flow but displays moderate risk indicators "
                f"(Health Score: {score:.1f}/100, Default Probability: {def_prob:.1f}%). Monthly covenant compliance validation required."
            )
        else:
            recommendation = "CREDIT WATCH / DESTRUCTIVE RESTRUCTURE REQUIRED"
            recommendation_reason = (
                f"Elevated default risk detected for {company_name} (Default Probability: {def_prob:.1f}%, Health Score: {score:.1f}/100). "
                "Immediate review of liquidity covenants and leverage limits is advised."
            )

        return {
            "title": f"Executive Credit Memorandum — {company_name}",
            "generated_at": borrower.get("updated_at") or "Live Real-Time Generation",
            "borrower": {
                "id": borrower.get("id", ""),
                "company_name": company_name,
                "sector": sector,
                "country": country,
            },
            "summary": {
                "health_score": score,
                "health_category": category,
                "default_probability": def_prob,
                "default_risk_category": risk_category,
                "recommendation": recommendation,
                "recommendation_reason": recommendation_reason,
            },
            "financial_highlights": {
                "revenue": financials.get("revenue"),
                "ebitda": financials.get("ebitda"),
                "net_income": financials.get("net_income"),
                "total_debt": financials.get("total_debt"),
                "cash": financials.get("cash"),
                "leverage_ratio": financials.get("leverage_ratio"),
                "interest_coverage": financials.get("interest_coverage"),
                "currency": financials.get("currency", "USD"),
            },
            "covenant_summary": {
                "total_monitored": len(covenants),
                "healthy_count": len(compliant_covenants),
                "breach_count": len(breached_covenants),
                "breached_details": breached_covenants,
                "all_covenants": covenants,
            },
            "risk_factors": default_pred.get("risk_factors") or [
                "No specific risk factors uploaded yet.",
            ],
        }
