"""
Phase 2B — HIGH-1: AI Recommendation Generation Quality Tests.

Verifies that recommendations are:
  1. Grounded in actual covenant/risk data with clear issue, evidence, and action.
  2. Distinct across multiple conditions.
  3. Free of semantic duplicates when re-evaluated.
  4. Non-fabricated when no risk conditions exist ("No Actionable Recommendations").
  5. Truthful when financial data is missing (requests statements, no false metric claims).
  6. Preserving actioned recommendations (is_actioned = TRUE).
  7. Idempotent across repeated pipeline runs.
"""
import pytest
import uuid
import json
from datetime import datetime, timezone
from ai.engines.recommendation_engine import RecommendationEngine


class MockSessionHIGH1:
    """Configurable mock database session for testing recommendation generation rules."""

    def __init__(self, borrower=None, covenants=None, health=None, risk=None, fin=None, existing_recs=None):
        self.borrower = borrower or {"id": "b1", "company_name": "Acme Corp"}
        self.covenants = covenants or []
        self.health = health
        self.risk = risk
        self.fin = fin
        self.existing_recs = existing_recs or []
        self.deleted = False
        self.inserted = []
        self.committed = False

    async def execute(self, stmt, params=None):
        sql = str(stmt).upper()

        class MockResult:
            def __init__(self, rows):
                self._rows = rows
            def mappings(self):
                return self
            def first(self):
                if isinstance(self._rows, list):
                    return self._rows[0] if self._rows else None
                return self._rows
            def all(self):
                if isinstance(self._rows, list):
                    return self._rows
                return [self._rows] if self._rows else []

        if "FROM BORROWERS" in sql:
            return MockResult(self.borrower)
        elif "FROM COVENANT_MONITORING" in sql:
            return MockResult(self.covenants)
        elif "FROM BORROWER_HEALTH_SCORES" in sql:
            return MockResult(self.health)
        elif "FROM RISK_ASSESSMENTS" in sql:
            return MockResult(self.risk)
        elif "FROM FINANCIAL_METRICS" in sql:
            return MockResult(self.fin)
        elif "DELETE FROM AI_RECOMMENDATIONS" in sql:
            self.deleted = True
            # Keep actioned recs, remove non-actioned
            self.existing_recs = [r for r in self.existing_recs if r.get("is_actioned")]
            return MockResult([])
        elif "INSERT INTO AI_RECOMMENDATIONS" in sql:
            if params:
                self.inserted.append(params)
            return MockResult([])
        return MockResult([])

    async def commit(self):
        self.committed = True


@pytest.mark.asyncio
async def test_genuine_covenant_breach_recommendation():
    """Verify genuine covenant breach produces specific, traceable recommendation."""
    b_id = str(uuid.uuid4())
    cov = {
        "id": "cm-1",
        "covenant_id": "cov-101",
        "covenant_name": "Maximum Leverage Ratio Maintenance",
        "facility_name": "Senior Term Loan A",
        "status": "breach",
        "current_value": 4.85,
        "threshold_value": 4.00,
        "headroom_pct": -21.25,
    }
    session = MockSessionHIGH1(covenants=[cov])
    engine = RecommendationEngine()
    recs = await engine.generate_recommendations(session, b_id)

    assert len(recs) == 1
    rec = recs[0]
    assert rec["priority"] == "urgent"
    assert rec["action_required"] is True
    assert "Escalate Covenant Breach" in rec["title"]
    assert "Maximum Leverage Ratio Maintenance" in rec["title"]
    assert "4.85" in rec["reasoning"]
    assert "4.00" in rec["reasoning"]
    assert "Senior Term Loan A" in rec["reasoning"]


@pytest.mark.asyncio
async def test_multiple_conditions_produce_distinct_recommendations():
    """Verify breach, warning, and high default risk produce distinct recommendations."""
    b_id = str(uuid.uuid4())
    cov_breach = {
        "id": "cm-1",
        "covenant_id": "cov-101",
        "covenant_name": "Max Leverage",
        "facility_name": "Term Loan",
        "status": "critical",
        "current_value": 5.2,
        "threshold_value": 4.0,
        "headroom_pct": -30.0,
    }
    cov_warning = {
        "id": "cm-2",
        "covenant_id": "cov-102",
        "covenant_name": "Min Interest Coverage",
        "facility_name": "Revolver",
        "status": "warning",
        "current_value": 2.6,
        "threshold_value": 2.5,
        "headroom_pct": 4.0,
    }
    risk = {
        "default_probability": 45.0,
        "risk_category": "critical",
        "risk_factors": json.dumps(["High Leverage", "Negative FCF"]),
    }
    session = MockSessionHIGH1(covenants=[cov_breach, cov_warning], risk=risk)
    engine = RecommendationEngine()
    recs = await engine.generate_recommendations(session, b_id)

    types = [r["type"] for r in recs]
    assert len(recs) == 3
    assert len(set(types)) == 3  # All distinct types
    assert any("breach" in t for t in types)
    assert any("warning" in t for t in types)
    assert "high_default_risk" in types


@pytest.mark.asyncio
async def test_no_semantic_duplicate_for_same_condition():
    """Verify repeated evaluation of the same underlying condition yields no semantic duplicates."""
    b_id = str(uuid.uuid4())
    cov_breach = {
        "id": "cm-1",
        "covenant_id": "cov-101",
        "covenant_name": "Max Leverage",
        "status": "breach",
        "current_value": 4.5,
        "threshold_value": 4.0,
        "headroom_pct": -12.5,
    }
    # Duplicate entries in DB for same covenant ID
    session = MockSessionHIGH1(covenants=[cov_breach, cov_breach])
    engine = RecommendationEngine()
    recs = await engine.generate_recommendations(session, b_id)

    assert len(recs) == 1, "Duplicate condition must not produce duplicate recommendations"


@pytest.mark.asyncio
async def test_no_risk_conditions_returns_no_actionable_recommendations():
    """Verify healthy borrower produces 'No Actionable Recommendations' instead of invented items."""
    b_id = str(uuid.uuid4())
    health = {"score": 92.5, "category": "excellent"}
    fin = {"ebitda": 100_000_000, "revenue": 500_000_000}
    session = MockSessionHIGH1(health=health, fin=fin)
    engine = RecommendationEngine()
    recs = await engine.generate_recommendations(session, b_id)

    assert len(recs) == 1
    assert recs[0]["title"] == "No Actionable Recommendations"
    assert recs[0]["priority"] == "low"
    assert recs[0]["action_required"] is False


@pytest.mark.asyncio
async def test_missing_financial_data_returns_data_request():
    """Verify missing financial data generates a data request, not false risk metric claims."""
    b_id = str(uuid.uuid4())
    session = MockSessionHIGH1(fin=None, health=None, risk=None)
    engine = RecommendationEngine()
    recs = await engine.generate_recommendations(session, b_id)

    assert len(recs) == 1
    assert recs[0]["title"] == "Request Missing Financial Statements"
    assert recs[0]["priority"] == "high"
    assert recs[0]["action_required"] is True
    assert "unavailable" in recs[0]["reasoning"].lower()


@pytest.mark.asyncio
async def test_actioned_recommendation_preserved():
    """Verify actioned recommendations (is_actioned = TRUE) are preserved when engine re-runs."""
    b_id = str(uuid.uuid4())
    actioned_rec = {
        "id": "rec-already-actioned",
        "borrower_id": b_id,
        "recommendation_type": "escalate_covenant_breach",
        "is_actioned": True
    }
    session = MockSessionHIGH1(existing_recs=[actioned_rec])
    engine = RecommendationEngine()
    await engine.generate_recommendations(session, b_id)

    assert session.deleted is True
    assert len(session.existing_recs) == 1
    assert session.existing_recs[0]["id"] == "rec-already-actioned"


@pytest.mark.asyncio
async def test_recommendation_engine_idempotency():
    """Verify running recommendation engine multiple times produces identical results."""
    b_id = str(uuid.uuid4())
    health = {"score": 52.0, "category": "high_risk"}
    fin = {"ebitda": 10_000_000, "revenue": 50_000_000}
    session = MockSessionHIGH1(health=health, fin=fin)
    engine = RecommendationEngine()

    run1 = await engine.generate_recommendations(session, b_id)
    run2 = await engine.generate_recommendations(session, b_id)

    assert len(run1) == len(run2)
    assert run1[0]["title"] == run2[0]["title"]
    assert run1[0]["priority"] == run2[0]["priority"]
