"""
PostgreSQL structured SQL retriever.
Queries covenants and financial_metrics tables for structured context.
"""
from typing import Any, List
import structlog
from ai.rag.retrievers.base_retriever import BaseRetriever
from integrations.postgres.client import PostgresClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class SqlRetriever(BaseRetriever):
    """
    Retrieves structured covenant and financial data from PostgreSQL
    to complement vector and graph results in Hybrid RAG.
    """

    def __init__(self, postgres_client: PostgresClient | None = None) -> None:
        self._client = postgres_client or PostgresClient(
            database_url=settings.DATABASE_URL,
            pool_size=3,
            max_overflow=2,
        )
        self._client.initialize()

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("sql.retrieve", query=query, limit=limit)

        borrower_id = kwargs.get("borrower_id")
        agreement_id = kwargs.get("agreement_id")

        results: List[dict] = []

        try:
            async with self._client.session() as session:
                from sqlalchemy import text

                # ── Covenants ────────────────────────────────────────
                if borrower_id:
                    cov_result = await session.execute(
                        text("""
                            SELECT name, covenant_type, formula, threshold, threshold_direction,
                                   frequency, cure_period_days, is_event_of_default, raw_text
                            FROM covenants
                            WHERE borrower_id = :borrower_id
                            LIMIT :limit
                        """),
                        {"borrower_id": borrower_id, "limit": limit},
                    )
                elif agreement_id:
                    cov_result = await session.execute(
                        text("""
                            SELECT name, covenant_type, formula, threshold, threshold_direction,
                                   frequency, cure_period_days, is_event_of_default, raw_text
                            FROM covenants
                            WHERE agreement_id = :agreement_id
                            LIMIT :limit
                        """),
                        {"agreement_id": agreement_id, "limit": limit},
                    )
                else:
                    # Keyword text search fallback
                    cov_result = await session.execute(
                        text("""
                            SELECT name, covenant_type, formula, threshold, threshold_direction,
                                   frequency, cure_period_days, is_event_of_default, raw_text
                            FROM covenants
                            WHERE LOWER(name) LIKE :pattern OR LOWER(formula) LIKE :pattern
                            LIMIT :limit
                        """),
                        {"pattern": f"%{query.lower()}%", "limit": limit},
                    )

                for row in cov_result.mappings():
                    d = dict(row)
                    results.append({
                        "source": "postgres_covenants",
                        "content": (
                            f"Covenant: {d.get('name')} | Type: {d.get('covenant_type')} "
                            f"| Threshold: {d.get('threshold')} ({d.get('threshold_direction', 'N/A')}) "
                            f"| Frequency: {d.get('frequency')}"
                        ),
                        "score": 0.85,
                        "metadata": d,
                    })

                # ── Financial Metrics ────────────────────────────────
                if borrower_id or agreement_id:
                    fin_filter = "borrower_id = :filter_id" if borrower_id else "agreement_id = :filter_id"
                    filter_id = borrower_id or agreement_id
                    fin_result = await session.execute(
                        text(f"""
                            SELECT reporting_period, revenue, ebitda, net_income,
                                   total_debt, cash, interest_expense,
                                   leverage_ratio, interest_coverage, currency
                            FROM financial_metrics
                            WHERE {fin_filter}
                            ORDER BY extracted_at DESC
                            LIMIT 3
                        """),
                        {"filter_id": filter_id},
                    )
                    for row in fin_result.mappings():
                        d = dict(row)
                        results.append({
                            "source": "postgres_financials",
                            "content": (
                                f"Period: {d.get('reporting_period')} "
                                f"| EBITDA: {d.get('ebitda')} | Debt: {d.get('total_debt')} "
                                f"| Leverage: {d.get('leverage_ratio')} "
                                f"| Coverage: {d.get('interest_coverage')}"
                            ),
                            "score": 0.80,
                            "metadata": d,
                        })

        except Exception as exc:
            logger.error("sql.retrieve_failed", error=str(exc))

        return results
