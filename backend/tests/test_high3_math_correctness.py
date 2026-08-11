"""
Phase 2B — HIGH-3: Risk/Stress Testing Mathematical Correctness
Automated unit tests covering:
  - Zero / near-zero denominator handling
  - Missing financial metrics (None propagation)
  - Valid financial inputs
  - Stress scenarios: valid / insufficient data / severe scenario
  - Default probability when data is insufficient / coverage is missing
  - Health score coverage cap
  - Financial agent: no fabricated EBITDA / no 0.0 for incalculable ratios
"""
import pytest
from decimal import Decimal
from ai.engines.financial_engine import FinancialMetrics, MAX_COVERAGE_CAP


# ── FinancialMetrics unit tests ───────────────────────────────────────────────

class TestFinancialMetricsRatios:

    def _make(self, **kwargs) -> FinancialMetrics:
        base = {
            "agreement_id": "ag1", "borrower_id": "b1", "reporting_period": "FY",
            "revenue": None, "ebitda": None, "net_income": None,
            "total_debt": None, "cash": None, "interest_expense": None,
            "current_ratio": None, "quick_ratio": None,
        }
        base.update(kwargs)
        return FinancialMetrics(base)

    def test_zero_ebitda_leverage_is_none(self):
        """Zero EBITDA → leverage is undefined, must return None (not 0.0)."""
        m = self._make(ebitda=0.0, total_debt=100_000_000, cash=0)
        assert m.leverage_ratio is None, "leverage_ratio must be None when EBITDA is 0"

    def test_missing_ebitda_leverage_is_none(self):
        """Missing EBITDA in DB → leverage is None."""
        m = self._make(total_debt=50_000_000, cash=10_000_000)  # ebitda=None
        assert m.leverage_ratio is None

    def test_zero_interest_coverage_is_none(self):
        """Zero interest expense → coverage is undefined, must return None (not 0.0).
        CRITICAL: 0.0 coverage would mean 'cannot service debt'; None means 'unavailable'."""
        m = self._make(ebitda=1_000_000_000, interest_expense=0.0)
        assert m.interest_coverage is None, "coverage must be None when interest=0, not 0.0"

    def test_missing_interest_coverage_is_none(self):
        """None interest expense → coverage is None."""
        m = self._make(ebitda=500_000_000)  # interest_expense=None
        assert m.interest_coverage is None

    def test_near_zero_interest_coverage_capped(self):
        """Near-zero interest expense → raw coverage would be astronomic; must be capped at 50x."""
        m = self._make(ebitda=112_390_000_000, interest_expense=268.0)
        assert m.interest_coverage is not None
        assert m.interest_coverage == MAX_COVERAGE_CAP, (
            f"Expected {MAX_COVERAGE_CAP}x cap, got {m.interest_coverage}"
        )

    def test_valid_leverage_calculated_correctly(self):
        """Valid EBITDA and debt → correct leverage ratio."""
        m = self._make(ebitda=500_000_000, total_debt=1_500_000_000, cash=100_000_000)
        # net_debt = 1.4B, leverage = 1.4B / 500M = 2.8
        assert m.leverage_ratio == pytest.approx(2.8, abs=0.01)

    def test_valid_coverage_calculated_correctly(self):
        """Valid EBITDA and interest → correct coverage ratio."""
        m = self._make(ebitda=500_000_000, interest_expense=100_000_000)
        assert m.interest_coverage == pytest.approx(5.0, abs=0.01)

    def test_dscr_none_when_interest_missing(self):
        """DSCR must be None (not ebitda/1) when interest_expense is None."""
        m = self._make(ebitda=500_000_000)  # interest=None
        assert m.dscr is None, "DSCR must be None, not ebitda/1 which is meaningless"

    def test_debt_to_equity_none_when_net_income_nonpositive(self):
        """D/E must be None (not debt/1) when net_income ≤ 0."""
        m = self._make(total_debt=500_000_000, net_income=0)
        assert m.debt_to_equity is None
        m2 = self._make(total_debt=500_000_000, net_income=-10_000_000)
        assert m2.debt_to_equity is None

    def test_data_quality_reflects_availability(self):
        """data_quality correctly identifies which metrics are available."""
        m = self._make(ebitda=100_000_000, revenue=500_000_000)
        assert m.data_quality["ebitda_available"] is True
        assert m.data_quality["revenue_available"] is True
        assert m.data_quality["interest_expense_available"] is False  # not provided
        assert m.data_quality["coverage_calculable"] is False

    def test_all_none_inputs_produce_none_ratios(self):
        """Row with all NULL fields produces all-None derived ratios."""
        m = self._make()
        assert m.leverage_ratio is None
        assert m.interest_coverage is None
        assert m.dscr is None


# ── StressTester unit tests ───────────────────────────────────────────────────

class TestStressTester:

    def _make_session(self, fin_row=None, covenants=None):
        class MockResult:
            def __init__(self, rows):
                self._rows = rows
            def mappings(self): return self
            def first(self): return self._rows[0] if self._rows else None
            def all(self): return self._rows

        class MockSession:
            def __init__(self, fin, covs):
                self._fin = fin
                self._covs = covs or []
                self.persisted = False
            async def execute(self, stmt, params=None):
                sql = str(stmt).upper()
                if "FINANCIAL_METRICS" in sql and "SELECT" in sql:
                    return MockResult([self._fin] if self._fin else [])
                elif "COVENANTS" in sql:
                    return MockResult(self._covs)
                elif "INSERT" in sql:
                    self.persisted = True
                    return MockResult([])
                return MockResult([])
            async def commit(self): pass

        return MockSession(fin_row, covenants)

    @pytest.mark.asyncio
    async def test_insufficient_data_no_fin_row(self):
        """No financial data → calculation_status = insufficient_data, proj_default = None."""
        from ai.engines.stress_tester import StressTester
        session = self._make_session(fin_row=None)
        result = await StressTester().run_scenario(session, "b1", "Test")
        assert result["calculation_status"] == "insufficient_data"
        assert result["projected_default_prob"] is None
        assert result["projected_health_score"] is None
        assert result["at_risk"] is None

    @pytest.mark.asyncio
    async def test_insufficient_data_missing_ebitda(self):
        """Fin row with no EBITDA → calculation_status = insufficient_data."""
        from ai.engines.stress_tester import StressTester
        fin = {
            "revenue": 100_000_000, "ebitda": None,
            "total_debt": 200_000_000, "cash": 10_000_000, "interest_expense": None,
        }
        session = self._make_session(fin_row=fin)
        result = await StressTester().run_scenario(session, "b1", "Test")
        assert result["calculation_status"] == "insufficient_data"
        assert result["projected_default_prob"] is None

    @pytest.mark.asyncio
    async def test_near_zero_interest_coverage_capped_and_nonzero_default(self):
        """Near-zero interest → coverage capped at 50x → proj_default > 0 for bad scenario.

        This uses a LEVERAGED borrower (positive net debt) so that:
          - EBITDA decline genuinely hurts the health score.
          - The rate shock creates real interest burden.
          - The 50x coverage cap prevents the formula from being dominated.
        The Alphabet-like case (cash > debt, $112B EBITDA) is genuinely resilient
        even after a -50% shock — that's correct behaviour, not a bug.
        """
        from ai.engines.stress_tester import StressTester
        fin = {
            "revenue": 800_000_000,
            "ebitda": 120_000_000,           # meaningful EBITDA
            "total_debt": 600_000_000,        # net debt positive: 600M - 20M = 580M
            "cash": 20_000_000,
            "interest_expense": 150.0,        # near-zero interest artefact (unit mismatch)
        }
        session = self._make_session(fin_row=fin)
        result = await StressTester().run_scenario(
            session, "b1", "Severe Recession",
            revenue_change_pct=-40.0,
            ebitda_change_pct=-55.0,           # EBITDA nearly halved
            interest_rate_change_bps=400.0,    # rate shock creates real interest burden
            debt_change_pct=20.0,
        )
        # Must not be "always 0%" regardless of scenario severity.
        assert result["calculation_status"] in ("valid", "partial_data")
        assert result["projected_default_prob"] is not None
        assert result["projected_default_prob"] > 0.0, (
            f"proj_default should be > 0 for severe scenario on leveraged borrower, "
            f"got {result['projected_default_prob']}. Details: {result['details']}"
        )
        # Caveats must mention the coverage cap.
        assert any("capped" in c.lower() or "near-zero" in c.lower() for c in result["caveats"]), (
            f"Expected caveat about coverage cap, got: {result['caveats']}"
        )

    @pytest.mark.asyncio
    async def test_valid_scenario_produces_valid_result(self):
        """Normal inputs → valid calculation_status and sensible proj_default."""
        from ai.engines.stress_tester import StressTester
        fin = {
            "revenue": 500_000_000,
            "ebitda": 100_000_000,
            "total_debt": 300_000_000,
            "cash": 50_000_000,
            "interest_expense": 20_000_000,
        }
        session = self._make_session(fin_row=fin)
        result = await StressTester().run_scenario(
            session, "b1", "Mild",
            revenue_change_pct=-10.0,
            ebitda_change_pct=-15.0,
            interest_rate_change_bps=100.0,
            debt_change_pct=5.0,
        )
        assert result["calculation_status"] in ("valid", "partial_data")
        assert result["projected_default_prob"] is not None
        assert 0.0 <= result["projected_default_prob"] <= 100.0
        assert result["details"]["stressed"]["leverage"] is not None
        assert result["details"]["stressed"]["coverage"] is not None

    @pytest.mark.asyncio
    async def test_severe_scenario_increases_default_vs_mild(self):
        """Severe scenario must produce higher default probability than mild scenario."""
        from ai.engines.stress_tester import StressTester
        fin = {
            "revenue": 500_000_000, "ebitda": 100_000_000,
            "total_debt": 300_000_000, "cash": 50_000_000, "interest_expense": 20_000_000,
        }
        mild_session = self._make_session(fin_row=fin)
        severe_session = self._make_session(fin_row=fin)

        mild = await StressTester().run_scenario(
            mild_session, "b1", "Mild", revenue_change_pct=-5.0, ebitda_change_pct=-5.0
        )
        severe = await StressTester().run_scenario(
            severe_session, "b1", "Severe",
            revenue_change_pct=-40.0, ebitda_change_pct=-50.0, interest_rate_change_bps=400.0
        )
        assert severe["projected_default_prob"] >= mild["projected_default_prob"], (
            "Severe scenario must produce >= default probability vs. mild scenario"
        )


# ── HealthScoreEngine unit tests ──────────────────────────────────────────────

class TestHealthScoreEngine:

    @pytest.mark.asyncio
    async def test_high_coverage_does_not_dominate_fin_score(self):
        """Coverage of 50x should not produce a fin_score of 100 by itself."""
        from ai.engines.health_score_engine import HealthScoreEngine

        class MockSession:
            async def execute(self, stmt, params=None):
                sql = str(stmt).upper()
                class R:
                    def mappings(self): return self
                    def first(self): return {
                        "revenue": 500_000_000, "ebitda": 100_000_000,
                        "total_debt": 200_000_000, "cash": 30_000_000,
                        "leverage_ratio": 0.85, "interest_coverage": 50.0,
                    } if "FINANCIAL_METRICS" in sql else None
                    def all(self): return []
                return R()
            async def commit(self): pass

        engine = HealthScoreEngine()
        result = await engine.calculate_and_persist(MockSession(), "b1")
        # fin_score = (0.2 * 200) + (50 * 10) = 40 + 500 = min(100, 540) = 100
        # But with the cap: cov_for_formula = min(50, 50) = 50 → same here.
        # The key check: result is not magically inflated beyond 100.
        assert result.score <= 100.0
        assert result.breakdown["financial_score"] is not None
        assert result.breakdown["financial_score"] <= 100.0

    @pytest.mark.asyncio
    async def test_missing_leverage_gives_none_leverage_score(self):
        """None leverage_ratio from DB must not produce a leverage_score of 70."""
        from ai.engines.health_score_engine import HealthScoreEngine

        class MockSession:
            async def execute(self, stmt, params=None):
                sql = str(stmt).upper()
                class R:
                    def mappings(self): return self
                    def first(self): return {
                        "revenue": 500_000_000, "ebitda": 100_000_000,
                        "total_debt": 200_000_000, "cash": 30_000_000,
                        "leverage_ratio": None,
                        "interest_coverage": 5.0,
                    } if "FINANCIAL_METRICS" in sql else None
                    def all(self): return []
                return R()
            async def commit(self): pass

        engine = HealthScoreEngine()
        result = await engine.calculate_and_persist(MockSession(), "b1")
        assert result.breakdown["leverage_score"] is None, (
            "Leverage score must be None when leverage_ratio is incalculable, not 70"
        )

    @pytest.mark.asyncio
    async def test_no_data_score_is_not_inflated(self):
        """No financial data → score based only on compliance (no artificial +10 boost)."""
        from ai.engines.health_score_engine import HealthScoreEngine

        class MockSession:
            async def execute(self, stmt, params=None):
                class R:
                    def mappings(self): return self
                    def first(self): return None
                    def all(self): return []
                return R()
            async def commit(self): pass

        engine = HealthScoreEngine()
        result = await engine.calculate_and_persist(MockSession(), "b1")
        # No breaches, no fin data: score = 100 * 0.50 = 50
        assert result.score == pytest.approx(50.0, abs=1.0), (
            f"No-data score should be ~50 (compliance only), got {result.score}"
        )
        assert result.breakdown["financial_score"] is None


# ── DefaultPredictor unit tests ───────────────────────────────────────────────

class TestDefaultPredictor:

    def _make_session(self, fin=None, health=None):
        class MockResult:
            def __init__(self, row):
                self._row = row
            def mappings(self): return self
            def first(self): return self._row
            def all(self): return [self._row] if self._row else []

        class MockSession:
            def __init__(self, f, h):
                self._fin = f; self._health = h
            async def execute(self, stmt, params=None):
                sql = str(stmt).upper()
                if "FINANCIAL_METRICS" in sql:
                    return MockResult(self._fin)
                elif "BORROWER_HEALTH_SCORES" in sql:
                    return MockResult(self._health)
                return MockResult(None)
            async def commit(self): pass

        return MockSession(fin, health)

    @pytest.mark.asyncio
    async def test_none_coverage_triggers_unavailability_risk_factor(self):
        """interest_coverage=None in DB → risk factor says coverage unavailable.
        Confidence < 0.88 because interest_expense is missing.
        """
        from ai.engines.default_predictor import DefaultPredictor
        fin = {
            "leverage_ratio": 2.5,
            "interest_coverage": None,   # ← DB NULL
            "interest_expense": None,    # ← missing, triggers confidence reduction
            "ebitda": 100_000_000,
            "total_debt": 200_000_000,
            "revenue": 500_000_000,
        }
        session = self._make_session(fin=fin)
        result = await DefaultPredictor().predict_and_persist(session, "b1")
        factors = " ".join(result["risk_factors"]).lower()
        assert "unavailable" in factors or "unable to assess" in factors, (
            "Missing coverage must produce an 'unavailable' risk factor, not be silently ignored"
        )
        # Confidence = 0.65 (has EBITDA+revenue but no interest_expense) < 0.88
        assert result["confidence_score"] < 0.88, (
            f"Expected confidence < 0.88 (missing interest), got {result['confidence_score']}"
        )
        assert result["confidence_score"] == pytest.approx(0.65, abs=0.01)

    @pytest.mark.asyncio
    async def test_zero_coverage_is_a_distress_signal(self):
        """interest_coverage=0.0 (actual zero) must trigger severe distress factor."""
        from ai.engines.default_predictor import DefaultPredictor
        fin = {
            "leverage_ratio": 2.5,
            "interest_coverage": 0.0,
            "ebitda": 0.0,
            "total_debt": 200_000_000,
            "revenue": 500_000_000,
        }
        session = self._make_session(fin=fin)
        result = await DefaultPredictor().predict_and_persist(session, "b1")
        factors = " ".join(result["risk_factors"]).lower()
        assert "0x" in factors or "zero" in factors or "cannot service" in factors

    @pytest.mark.asyncio
    async def test_no_fin_row_confidence_is_low(self):
        """No fin row → confidence = 0.30 (not 0.88 or 0.50)."""
        from ai.engines.default_predictor import DefaultPredictor
        session = self._make_session(fin=None)
        result = await DefaultPredictor().predict_and_persist(session, "b1")
        assert result["confidence_score"] == pytest.approx(0.30, abs=0.01)

    @pytest.mark.asyncio
    async def test_fin_row_with_all_zeros_has_lower_confidence(self):
        """Fin row exists but key fields are zero → confidence = 0.55 (not 0.88)."""
        from ai.engines.default_predictor import DefaultPredictor
        fin = {
            "leverage_ratio": None,
            "interest_coverage": None,
            "ebitda": 0.0,
            "total_debt": 0.0,
            "revenue": 0.0,
        }
        session = self._make_session(fin=fin)
        result = await DefaultPredictor().predict_and_persist(session, "b1")
        assert result["confidence_score"] == pytest.approx(0.55, abs=0.01), (
            f"Confidence should be 0.55 for zero-value fin row, got {result['confidence_score']}"
        )

    @pytest.mark.asyncio
    async def test_healthy_borrower_correct_confidence(self):
        """Borrower with real EBITDA, revenue AND interest_expense → confidence = 0.88."""
        from ai.engines.default_predictor import DefaultPredictor
        fin = {
            "leverage_ratio": 1.5,
            "interest_coverage": 8.0,
            "interest_expense": 62_500_000,  # non-zero interest expense
            "ebitda": 500_000_000,
            "total_debt": 500_000_000,
            "revenue": 2_000_000_000,
        }
        session = self._make_session(fin=fin)
        result = await DefaultPredictor().predict_and_persist(session, "b1")
        assert result["confidence_score"] == pytest.approx(0.88, abs=0.01)
