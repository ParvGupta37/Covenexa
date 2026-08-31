"""
PostgreSQL structured SQL retriever.
Queries borrower profile, health score, covenant monitoring, risk assessment,
and financial_metrics tables for structured context.
"""
import json
from typing import Any, List
import structlog
from ai.rag.retrievers.base_retriever import BaseRetriever
from integrations.postgres.client import PostgresClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


def _fmt_val(val: Any, unit: str = "", money: bool = False, ratio: bool = False) -> str:
    """Format numeric value or return N/A if None (never converts None to 0)."""
    if val is None:
        return "N/A"
    try:
        num = float(val)
        if money:
            if abs(num) >= 1_000_000_000_000:
                return f"${num / 1_000_000_000_000:.2f}T"
            elif abs(num) >= 1_000_000_000:
                return f"${num / 1_000_000_000:.2f}B"
            elif abs(num) >= 1_000_000:
                return f"${num / 1_000_000:.2f}M"
            return f"${num:,.2f}"
        if ratio:
            return f"{num:.2f}x"
        return f"{num:.1f}{unit}"
    except (ValueError, TypeError):
        return str(val) if val else "N/A"


def _clean_json_str(val: Any) -> str:
    """Formats JSON strings into human-readable text."""
    if not val:
        return "N/A"
    if isinstance(val, str) and (val.startswith("{") or val.startswith("[")):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return "; ".join(str(x) for x in parsed)
            elif isinstance(parsed, dict):
                parts = [f"{k.replace('_', ' ').title()}: {v}" for k, v in parsed.items() if v is not None]
                return "; ".join(parts) if parts else "N/A"
        except Exception:
            pass
    return str(val)


class SqlRetriever(BaseRetriever):
    """
    Retrieves structured credit risk, health, covenant, and financial data
    from PostgreSQL to complement vector and graph results in Hybrid RAG.
    """

    def __init__(self, postgres_client: PostgresClient | None = None) -> None:
        self._client = postgres_client

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("sql.retrieve", query=query, limit=limit)

        borrower_id = kwargs.get("borrower_id")
        session = kwargs.get("session")

        results: List[dict] = []

        # Handler logic executing against a session
        async def _query_with_session(sess):
            from sqlalchemy import text

            if not borrower_id:
                return []

            # 1. Borrower Entity Profile
            res_b = await sess.execute(
                text("SELECT id, company_name, sector, country, risk_rating_level, risk_rating_score FROM borrowers WHERE id = :b"),
                {"b": borrower_id}
            )
            b = res_b.mappings().first()
            if b:
                b_dict = dict(b)
                results.append({
                    "source": "postgres_sql",
                    "type": "borrower_profile",
                    "content": (
                        f"Borrower: {b_dict.get('company_name')} | Sector: {b_dict.get('sector')} "
                        f"| Country: {b_dict.get('country')} | Internal Rating: {_fmt_val(b_dict.get('risk_rating_level'))}"
                    ),
                    "score": 0.95,
                    "metadata": b_dict,
                })

            # 2. Latest Health Score
            res_h = await sess.execute(
                text("SELECT score, category, financial_score, compliance_score, liquidity_score, leverage_score, explanation FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
                {"b": borrower_id}
            )
            h = res_h.mappings().first()
            if h:
                h_dict = dict(h)
                explanation_clean = _clean_json_str(h_dict.get("explanation"))
                results.append({
                    "source": "postgres_sql",
                    "type": "health_score",
                    "content": (
                        f"Health Score: {_fmt_val(h_dict.get('score'))}/100 ({_fmt_val(h_dict.get('category')).upper()}) "
                        f"| Financial Score: {_fmt_val(h_dict.get('financial_score'))} "
                        f"| Compliance Score: {_fmt_val(h_dict.get('compliance_score'))} "
                        f"| Leverage Score: {_fmt_val(h_dict.get('leverage_score'))} "
                        f"| Breakdown: {explanation_clean}"
                    ),
                    "score": 0.92,
                    "metadata": h_dict,
                })

            # 3. Covenant Monitoring & Covenants (Deduplicated)
            res_cov = await sess.execute(
                text("""
                    SELECT DISTINCT ON (c.name) cm.status, cm.current_value, cm.threshold_value, cm.headroom_pct, cm.reason,
                           c.name as covenant_name, c.covenant_type, c.threshold_direction
                    FROM covenant_monitoring cm
                    JOIN covenants c ON c.id = cm.covenant_id
                    WHERE cm.borrower_id = :b
                    ORDER BY c.name, cm.checked_at DESC
                    LIMIT :limit
                """),
                {"b": borrower_id, "limit": limit}
            )
            covs = res_cov.mappings().all()
            if not covs:
                # Direct covenant fallback if monitoring hasn't recorded yet
                res_cov_direct = await sess.execute(
                    text("""
                        SELECT DISTINCT ON (c.name) 'UNKNOWN' as status, NULL as current_value, c.threshold as threshold_value, NULL as headroom_pct,
                               c.description as reason, c.name as covenant_name, c.covenant_type, c.threshold_direction
                        FROM covenants c
                        JOIN agreements a ON a.id = c.agreement_id
                        JOIN loans l ON l.id = a.loan_id
                        WHERE l.borrower_id = :b
                        ORDER BY c.name
                        LIMIT :limit
                    """),
                    {"b": borrower_id, "limit": limit}
                )
                covs = res_cov_direct.mappings().all()

            for c in covs:
                c_dict = dict(c)
                results.append({
                    "source": "postgres_sql",
                    "type": "covenant_monitoring",
                    "content": (
                        f"Covenant: {c_dict.get('covenant_name')} | Status: {str(c_dict.get('status')).upper()} "
                        f"| Current: {_fmt_val(c_dict.get('current_value'), ratio=True)} "
                        f"| Threshold: {_fmt_val(c_dict.get('threshold_value'), ratio=True)} ({c_dict.get('threshold_direction', 'max')}) "
                        f"| Headroom: {_fmt_val(c_dict.get('headroom_pct'), unit='%')} "
                        f"| Detail: {c_dict.get('reason') or 'Extracted agreement covenant parameter.'}"
                    ),
                    "score": 0.90,
                    "metadata": c_dict,
                })

            # 4. Default Risk Assessment
            res_risk = await sess.execute(
                text("SELECT default_probability, risk_category, confidence_score, z_score, risk_factors FROM risk_assessments WHERE borrower_id = :b ORDER BY assessed_at DESC LIMIT 1"),
                {"b": borrower_id}
            )
            r = res_risk.mappings().first()
            if r:
                r_dict = dict(r)
                risk_factors_clean = _clean_json_str(r_dict.get("risk_factors"))
                results.append({
                    "source": "postgres_sql",
                    "type": "risk_assessment",
                    "content": (
                        f"Default Probability: {_fmt_val(r_dict.get('default_probability'), unit='%')} "
                        f"| Category: {_fmt_val(r_dict.get('risk_category')).upper()} "
                        f"| Model Confidence: {_fmt_val(r_dict.get('confidence_score'))} "
                        f"| Z-Score: {_fmt_val(r_dict.get('z_score'))} "
                        f"| Risk Factors: {risk_factors_clean}"
                    ),
                    "score": 0.90,
                    "metadata": r_dict,
                })

            # 5. Financial Metrics
            res_fin = await sess.execute(
                text("SELECT reporting_period, revenue, ebitda, net_income, total_debt, net_debt, cash, interest_expense, leverage_ratio, interest_coverage, dscr FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
                {"b": borrower_id}
            )
            f = res_fin.mappings().first()
            if f:
                f_dict = dict(f)
                results.append({
                    "source": "postgres_sql",
                    "type": "financial_metrics",
                    "content": (
                        f"Financial Period: {f_dict.get('reporting_period', 'Latest')} "
                        f"| Revenue: {_fmt_val(f_dict.get('revenue'), money=True)} "
                        f"| EBITDA: {_fmt_val(f_dict.get('ebitda'), money=True)} "
                        f"| Total Debt: {_fmt_val(f_dict.get('total_debt'), money=True)} "
                        f"| Net Debt: {_fmt_val(f_dict.get('net_debt'), money=True)} "
                        f"| Cash: {_fmt_val(f_dict.get('cash'), money=True)} "
                        f"| Leverage Ratio: {_fmt_val(f_dict.get('leverage_ratio'), ratio=True)} "
                        f"| Interest Coverage: {_fmt_val(f_dict.get('interest_coverage'), ratio=True)} "
                        f"| DSCR: {_fmt_val(f_dict.get('dscr'), ratio=True)}"
                    ),
                    "score": 0.88,
                    "metadata": f_dict,
                })

            return results

        try:
            if session:
                return await _query_with_session(session)
            elif self._client:
                self._client.initialize()
                async with self._client.session() as sess:
                    return await _query_with_session(sess)
        except Exception as exc:
            logger.error("sql.retrieve_failed", error=str(exc))

        return results


# Canonical alias for case-insensitive naming compatibility
SQLRetriever = SqlRetriever
