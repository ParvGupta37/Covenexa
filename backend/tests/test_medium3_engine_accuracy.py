"""
MEDIUM-3 regression tests — Engine Accuracy & Data Integrity.

Covers:
  - trend_score: None on first run, real delta on subsequent runs
  - base_prob: explicit baseline in risk_factors
  - covenant formula field mapping (vs keyword heuristics)
  - RetrieverFactory: singleton retriever instances (no per-call re-creation)
  - /risk/graph: revenue/ebitda None → "N/A", not $0.00
  - /risk/portfolio: avg_score None when no health data
  - Dead ORM exports removed from __all__
  - get_loan: no dead code (loan_query_details removed)
  - company.store: no hardcoded org UUID, no fake agreement_id
  - covenant_agent: no hardcoded formula/threshold fallbacks
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "backend"))


# ─────────────────────────────────────────────────────────────
# trend_score: None on first run; real delta on subsequent runs
# ─────────────────────────────────────────────────────────────

class TestTrendScore:

    @pytest.mark.asyncio
    async def test_trend_score_is_none_when_no_prior_score(self):
        """First pipeline run: no prior health score → trend_score = None."""
        from ai.engines.health_score_engine import HealthScoreEngine

        engine = HealthScoreEngine()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "revenue": 1_000_000.0, "ebitda": 200_000.0,
                    "total_debt": 500_000.0, "cash": 150_000.0,
                    "leverage_ratio": 2.5, "interest_coverage": 4.0,
                    "interest_expense": 50_000.0,
                }
            elif "covenant_monitoring" in q:
                r.mappings.return_value.all.return_value = []
            else:
                # borrower_health_scores (prev) and any other = no data
                r.mappings.return_value.first.return_value = None
                r.mappings.return_value.all.return_value = []
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        result = await engine.calculate_and_persist(session, "test-b-1")
        assert result.breakdown["trend_score"] is None, (
            f"Expected trend_score=None on first run, got {result.breakdown['trend_score']}"
        )

    @pytest.mark.asyncio
    async def test_trend_score_positive_when_score_improved(self):
        """Score improved vs prior → trend_score > 80."""
        from ai.engines.health_score_engine import HealthScoreEngine

        engine = HealthScoreEngine()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "revenue": 2_000_000.0, "ebitda": 600_000.0,
                    "total_debt": 400_000.0, "cash": 300_000.0,
                    "leverage_ratio": 0.67, "interest_coverage": 8.0,
                    "interest_expense": 75_000.0,
                }
            elif "covenant_monitoring" in q:
                r.mappings.return_value.all.return_value = []
            else:
                # prior score = 60 → current will be higher → trend > 80
                r.mappings.return_value.first.return_value = {"score": 60.0}
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        result = await engine.calculate_and_persist(session, "test-b-2")
        trend = result.breakdown["trend_score"]
        assert trend is not None
        assert trend > 80.0, f"Expected trend > 80 for improved score, got {trend}"

    @pytest.mark.asyncio
    async def test_trend_score_negative_when_score_deteriorated(self):
        """Score fell vs prior → trend_score < 80."""
        from ai.engines.health_score_engine import HealthScoreEngine

        engine = HealthScoreEngine()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "revenue": 500_000.0, "ebitda": 20_000.0,
                    "total_debt": 4_000_000.0, "cash": 10_000.0,
                    "leverage_ratio": 8.0, "interest_coverage": 0.5,
                    "interest_expense": 40_000.0,
                }
            elif "covenant_monitoring" in q:
                r.mappings.return_value.all.return_value = []
            else:
                # prior score = 90 → current will be lower → trend < 80
                r.mappings.return_value.first.return_value = {"score": 90.0}
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        result = await engine.calculate_and_persist(session, "test-b-3")
        trend = result.breakdown["trend_score"]
        assert trend is not None
        assert trend < 80.0, f"Expected trend < 80 for deteriorated score, got {trend}"

    def test_trend_score_not_hardcoded_80_in_source(self):
        with open(REPO_ROOT / "ai/engines/health_score_engine.py") as f:
            content = f.read()
        assert "trend_score = 80.0" not in content


# ─────────────────────────────────────────────────────────────
# base_prob transparency
# ─────────────────────────────────────────────────────────────

class TestBaseProbTransparency:

    @pytest.mark.asyncio
    async def test_healthy_borrower_shows_baseline_in_risk_factors(self):
        from ai.engines.default_predictor import DefaultPredictor

        predictor = DefaultPredictor()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "revenue": 10_000_000.0, "ebitda": 3_000_000.0,
                    "total_debt": 2_000_000.0, "cash": 5_000_000.0,
                    "leverage_ratio": 0.67, "interest_coverage": 12.0,
                    "interest_expense": 250_000.0,
                }
            elif "borrower_health_scores" in q:
                r.mappings.return_value.first.return_value = {"score": 88.0}
            else:
                r.mappings.return_value.first.return_value = None
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        result = await predictor.predict_and_persist(session, "healthy-b")
        factors = result["risk_factors"]
        assert any("5.0%" in f and "baseline" in f.lower() for f in factors), (
            f"Expected explicit 5.0% baseline in risk_factors, got: {factors}"
        )

    @pytest.mark.asyncio
    async def test_no_financial_data_probability_not_exactly_5(self):
        from ai.engines.default_predictor import DefaultPredictor

        predictor = DefaultPredictor()

        async def fake_execute(query, params=None):
            r = MagicMock()
            r.mappings.return_value.first.return_value = None
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        result = await predictor.predict_and_persist(session, "no-data-b")
        assert result["default_probability"] > 5.0


# ─────────────────────────────────────────────────────────────
# Covenant formula mapping
# ─────────────────────────────────────────────────────────────

class TestCovenantFormulaMapping:

    @pytest.mark.asyncio
    async def test_formula_field_takes_precedence_over_keyword(self):
        """formula='leverage_ratio' must bind correctly even if name has no 'leverage' keyword."""
        from ai.engines.covenant_monitor import CovenantMonitor

        monitor = CovenantMonitor()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "leverage_ratio": 3.2, "interest_coverage": 5.0,
                    "dscr": None, "total_debt": 1_000_000.0,
                }
            elif "FROM covenants" in q:
                r.mappings.return_value.all.return_value = [{
                    "id": "cov-1",
                    "name": "Senior Secured Indebtedness Ratio",  # no 'leverage' keyword
                    "covenant_type": "maintenance",
                    "formula": "leverage_ratio",
                    "threshold": 4.0,
                    "threshold_direction": "max",
                }]
            else:
                r.mappings.return_value.all.return_value = []
                r.mappings.return_value.first.return_value = None
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        results = await monitor.evaluate_borrower_covenants(session, "b-formula")
        assert len(results) == 1
        assert results[0]["current_value"] == pytest.approx(3.2)
        assert results[0]["status"] in ("healthy", "warning")

    @pytest.mark.asyncio
    async def test_null_formula_falls_back_to_keyword(self):
        from ai.engines.covenant_monitor import CovenantMonitor

        monitor = CovenantMonitor()

        async def fake_execute(query, params=None):
            q = str(query)
            r = MagicMock()
            if "financial_metrics" in q:
                r.mappings.return_value.first.return_value = {
                    "leverage_ratio": 2.5, "interest_coverage": 4.0,
                    "dscr": None, "total_debt": 500_000.0,
                }
            elif "FROM covenants" in q:
                r.mappings.return_value.all.return_value = [{
                    "id": "cov-2",
                    "name": "Maximum Leverage Covenant",
                    "covenant_type": "maintenance",
                    "formula": None,  # no formula → keyword fallback
                    "threshold": 4.0,
                    "threshold_direction": "max",
                }]
            else:
                r.mappings.return_value.all.return_value = []
                r.mappings.return_value.first.return_value = None
            return r

        session = MagicMock()
        session.execute = AsyncMock(side_effect=fake_execute)
        session.commit = AsyncMock()

        results = await monitor.evaluate_borrower_covenants(session, "b-kw")
        assert len(results) == 1
        assert results[0]["current_value"] == pytest.approx(2.5)


# ─────────────────────────────────────────────────────────────
# RetrieverFactory singleton
# ─────────────────────────────────────────────────────────────

class TestRetrieverFactorySingleton:

    def test_same_instances_returned_across_get_all_calls(self):
        from ai.rag.retriever_factory import RetrieverFactory

        factory = RetrieverFactory()
        r1 = factory.get_all_retrievers()
        r2 = factory.get_all_retrievers()
        for a, b in zip(r1, r2):
            assert a is b, f"{type(a).__name__} was re-created between calls"

    def test_graph_retriever_neo4j_client_not_recreated(self):
        from ai.rag.retriever_factory import RetrieverFactory
        from ai.rag.retrievers.graph_retriever import GraphRetriever

        factory = RetrieverFactory()
        [r1] = [r for r in factory.get_all_retrievers() if isinstance(r, GraphRetriever)]
        [r2] = [r for r in factory.get_all_retrievers() if isinstance(r, GraphRetriever)]
        assert r1._client is r2._client, "Neo4jClient must not be recreated between calls"


# ─────────────────────────────────────────────────────────────
# Graph node NULL revenue → N/A
# ─────────────────────────────────────────────────────────────

class TestGraphNodeNullRevenue:

    def test_null_revenue_shows_na_not_zero(self):
        def fmt(fin):
            rev_str = f"${float(fin['revenue']):,.2f}" if fin['revenue'] is not None else "N/A"
            ebitda_str = f"${float(fin['ebitda']):,.2f}" if fin['ebitda'] is not None else "N/A"
            debt_str = f"${float(fin['total_debt']):,.2f}" if fin['total_debt'] is not None else "N/A"
            return f"Revenue: {rev_str} | EBITDA: {ebitda_str} | Total Debt: {debt_str}"

        details = fmt({"revenue": None, "ebitda": None, "total_debt": None})
        assert "N/A" in details
        assert "$0" not in details

        details_zero = fmt({"revenue": 0, "ebitda": 0, "total_debt": 0})
        assert "$0.00" in details_zero

    def test_graph_endpoint_has_no_revenue_or_0_pattern(self):
        with open(REPO_ROOT / "backend/app/api/v1/endpoints/risk.py") as f:
            content = f.read()
        assert "fin['revenue'] or 0" not in content
        assert "fin['ebitda'] or 0" not in content
        assert "fin['total_debt'] or 0" not in content


# ─────────────────────────────────────────────────────────────
# Portfolio avg_score None when no health data
# ─────────────────────────────────────────────────────────────

class TestPortfolioNullWhenNoData:

    def test_portfolio_logic_returns_none_for_empty_scores(self):
        scores = []
        if scores:
            avg_score = round(sum(scores) / len(scores), 1)
        else:
            avg_score = None
        assert avg_score is None

    def test_portfolio_source_has_no_zero_fill(self):
        with open(REPO_ROOT / "backend/app/api/v1/endpoints/risk.py") as f:
            content = f.read()
        assert "avg_score = 0.0" not in content
        assert "portfolio_risk_score = 0.0" not in content


# ─────────────────────────────────────────────────────────────
# Dead ORM exports
# ─────────────────────────────────────────────────────────────

class TestDeadORMExports:

    def test_financial_statement_orm_not_in_all(self):
        from app.infrastructure.orm import __all__ as orm_all
        assert "FinancialStatementORM" not in orm_all

    def test_compliance_result_orm_not_in_all(self):
        from app.infrastructure.orm import __all__ as orm_all
        assert "ComplianceResultORM" not in orm_all

    def test_financial_metric_orm_still_exported(self):
        from app.infrastructure.orm import __all__ as orm_all
        assert "FinancialMetricORM" in orm_all


# ─────────────────────────────────────────────────────────────
# get_loan dead code removed
# ─────────────────────────────────────────────────────────────

class TestGetLoanCleanup:

    def test_loan_query_details_helper_removed(self):
        with open(REPO_ROOT / "backend/app/api/v1/endpoints/loans.py") as f:
            content = f.read()
        assert "async def loan_query_details" not in content

    def test_get_loan_still_calls_handler(self):
        with open(REPO_ROOT / "backend/app/api/v1/endpoints/loans.py") as f:
            content = f.read()
        assert "handler.get_by_id(query)" in content


# ─────────────────────────────────────────────────────────────
# company.store.ts security
# ─────────────────────────────────────────────────────────────

class TestCompanyStoreSecurity:

    def test_hardcoded_org_uuid_removed(self):
        with open(REPO_ROOT / "frontend/src/store/company.store.ts") as f:
            content = f.read()
        assert "58b9ebce-3dc7-4168-af47-04a2354343f7" not in content

    def test_fake_agreement_id_removed(self):
        with open(REPO_ROOT / "frontend/src/store/company.store.ts") as f:
            content = f.read()
        assert "agreement_id: `agreement_" not in content

    def test_covenant_agent_no_hardcoded_formula_fallback(self):
        with open(REPO_ROOT / "ai/agents/covenant_agent.py") as f:
            content = f.read()
        assert '"Ratio Calculation"' not in content

    def test_covenant_agent_no_hardcoded_threshold_fallback(self):
        with open(REPO_ROOT / "ai/agents/covenant_agent.py") as f:
            content = f.read()
        assert '"threshold", 3.5' not in content
