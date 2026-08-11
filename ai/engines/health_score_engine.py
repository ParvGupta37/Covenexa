"""
Borrower Health Score Engine — Sprint 3 (Phase 2B: HIGH-3 fix).

RULES:
  - None ratio from financial_engine → omitted from formula (not treated as 0).
  - Coverage term is capped at MAX_COVERAGE_CAP before use in any formula.
  - No-data path does not give a gratuitous +10 baseline boost.
  - Calculated per-component; breakdown explicitly marks unavailable components.
Calculates borrower health score (0–100) based on weighted factors:
  - Financial Performance (30%)
  - Covenant Compliance  (25%)
  - Liquidity            (15%)
  - Leverage             (15%)
  - Historical Trend     (10%)
  - AI Confidence         (5%)
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = structlog.get_logger(__name__)

MAX_COVERAGE_CAP = 50.0


class HealthScoreResult:
    def __init__(self, score: float, category: str, breakdown: Dict[str, Any], explanation: str):
        self.score = round(score, 1)
        self.category = category
        self.breakdown = breakdown
        self.explanation = explanation


class HealthScoreEngine:
    """Calculates overall borrower health score and category strictly from real DB entries."""

    def _determine_category(self, score: float) -> str:
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "moderate"
        elif score >= 40:
            return "high_risk"
        else:
            return "critical"

    async def calculate_and_persist(self, session, borrower_id: str) -> HealthScoreResult:
        from sqlalchemy import text

        # ── 1. Fetch latest financial metrics ─────────────────────────────
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first()

        # ── 2. Fetch covenant breach / warning counts ──────────────────────
        res_cov = await session.execute(
            text("""
                SELECT status, COUNT(*) as cnt
                FROM covenant_monitoring
                WHERE borrower_id = :b
                GROUP BY status
            """),
            {"b": borrower_id}
        )
        cov_rows = res_cov.mappings().all()
        cov_counts = {r["status"]: r["cnt"] for r in cov_rows}
        breaches = cov_counts.get("breach", 0) + cov_counts.get("critical", 0)
        warnings = cov_counts.get("warning", 0)

        compliance_score = 100.0 - (breaches * 30.0) - (warnings * 10.0)
        compliance_score = max(0.0, min(100.0, compliance_score))

        # ── 3. Fetch previous health score for trend calculation ───────────
        # MEDIUM-3 fix: real trend from historical data; None on first run.
        # None = no prior data (not a fabricated neutral value).
        res_prev = await session.execute(
            text("""
                SELECT score FROM borrower_health_scores
                WHERE borrower_id = :b
                ORDER BY calculated_at DESC
                LIMIT 1
            """),
            {"b": borrower_id}
        )
        prev_row = res_prev.mappings().first()
        prev_score: Optional[float] = float(prev_row["score"]) if prev_row else None

        # ── 3. Compute component scores ────────────────────────────────────
        fin_score: Optional[float] = None
        leverage_score: Optional[float] = None
        liquidity_score: Optional[float] = None
        trend_score: Optional[float] = None
        ai_confidence_score: float = 50.0

        if fin:
            # Raw values — None preserved for denominator-sensitive fields.
            rev: float = float(fin["revenue"]) if fin.get("revenue") is not None else 0.0
            ebitda: Optional[float] = float(fin["ebitda"]) if fin.get("ebitda") is not None else None
            debt: float = float(fin["total_debt"]) if fin.get("total_debt") is not None else 0.0
            cash: float = float(fin["cash"]) if fin.get("cash") is not None else 0.0

            # Derived ratios — read from already-computed DB columns (may be NULL/None).
            leverage: Optional[float] = (
                float(fin["leverage_ratio"]) if fin.get("leverage_ratio") is not None else None
            )
            coverage: Optional[float] = (
                float(fin["interest_coverage"]) if fin.get("interest_coverage") is not None else None
            )

            # ── Financial score (margin + bounded coverage contribution) ────
            # Margin is always calculable if revenue > 0 and ebitda is not None.
            if ebitda is not None and rev > 0:
                margin = ebitda / rev
                # Coverage term: cap at MAX_COVERAGE_CAP before multiplying.
                # Without this cap a 419M× coverage → +4.19B pts → always 100.
                cov_for_formula = min(coverage, MAX_COVERAGE_CAP) if coverage is not None else 0.0
                fin_score = min(100.0, max(0.0, (margin * 200.0) + (cov_for_formula * 10.0)))
            elif ebitda is not None:
                # Have EBITDA but no revenue — use coverage only.
                cov_for_formula = min(coverage, MAX_COVERAGE_CAP) if coverage is not None else 0.0
                fin_score = min(100.0, max(0.0, 40.0 + (cov_for_formula * 5.0)))
            else:
                # EBITDA unavailable — financial score cannot be computed.
                fin_score = None

            # ── Leverage score ──────────────────────────────────────────────
            # None leverage (incalculable) ≠ zero leverage (perfect balance sheet).
            if leverage is not None:
                if leverage <= 2.0:
                    leverage_score = 95.0
                elif leverage <= 3.5:
                    leverage_score = 80.0
                elif leverage <= 5.0:
                    leverage_score = 60.0
                else:
                    leverage_score = 30.0
            else:
                # Leverage incalculable — cannot assign a good score.
                # Use neutral-low: 50 (neither penalised nor rewarded).
                leverage_score = None

            # ── Liquidity score ─────────────────────────────────────────────
            if debt > 0:
                liquidity_score = min(100.0, max(0.0, (cash / debt * 300.0)))
            elif cash > 0:
                liquidity_score = 90.0
            else:
                liquidity_score = 50.0

            trend_score = None  # Calculated below after total_score is known.
            # Confidence: high only if core metrics are present and non-zero.
            has_core = ebitda is not None and rev > 0
            ai_confidence_score = 90.0 if has_core else 60.0

        # ── 4. Weighted total score ────────────────────────────────────────
        if fin:
            # Use only calculable components; replace None with a neutral 50
            # but reduce the effective weight of missing components.
            def weighted(score: Optional[float], weight: float) -> tuple[float, float]:
                """Return (contributed_score, effective_weight)."""
                if score is None:
                    return 0.0, 0.0   # missing component contributes nothing
                return score * weight, weight

            pts_fin, w_fin         = weighted(fin_score, 0.30)
            pts_comp, w_comp       = (compliance_score * 0.25, 0.25)
            pts_liq, w_liq         = weighted(liquidity_score, 0.15)
            pts_lev, w_lev         = weighted(leverage_score, 0.15)
            pts_trend, w_trend     = weighted(trend_score, 0.10)
            pts_conf, w_conf       = (ai_confidence_score * 0.05, 0.05)

            total_weight = w_fin + w_comp + w_liq + w_lev + w_trend + w_conf

            if total_weight > 0:
                # Re-normalise so missing components don't deflate the score
                # below what the available information supports.
                total_score = (pts_fin + pts_comp + pts_liq + pts_lev + pts_trend + pts_conf) / total_weight
            else:
                total_score = 0.0
        else:
            # No financial data at all.
            # Score based purely on compliance — no gratuitous baseline boost.
            total_score = compliance_score * 0.50

        total_score = max(0.0, min(100.0, total_score))

        # ── 5. Compute trend score from historical delta (MEDIUM-3) ─────────
        # trend_score = None means "no prior run, no trend calculable".
        # When prior score exists, map delta to [0, 100]:
        #   delta > 0 (improving) → score > 80; delta < 0 (deteriorating) → score < 80.
        #   Capped so a +20pt jump still gives 100, -20pt gives 40.
        if prev_score is not None:
            delta = total_score - prev_score
            trend_score = max(0.0, min(100.0, 80.0 + (delta * 2.0)))
        else:
            trend_score = None  # First run — no trend data available.

        category = self._determine_category(total_score)

        # ── 5. Build breakdown (None for unavailable components) ───────────
        breakdown = {
            "financial_score":    round(fin_score, 1) if fin_score is not None else None,
            "compliance_score":   round(compliance_score, 1),
            "liquidity_score":    round(liquidity_score, 1) if liquidity_score is not None else None,
            "leverage_score":     round(leverage_score, 1) if leverage_score is not None else None,
            "trend_score":        round(trend_score, 1) if trend_score is not None else None,
            "ai_confidence_score": round(ai_confidence_score, 1),
        }

        explanation = (
            f"Health Score is {round(total_score, 1)} ({category.upper()}). "
            f"Financial performance: {f'{round(fin_score, 1)}/100' if fin_score is not None else 'N/A'}, "
            f"Compliance: {round(compliance_score, 1)}/100."
        )

        # ── 6. Persist to borrower_health_scores ────────────────────────────
        score_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        await session.execute(
            text("""
                INSERT INTO borrower_health_scores
                (id, borrower_id, score, category, financial_score, compliance_score,
                 liquidity_score, leverage_score, trend_score, explanation, calculated_at)
                VALUES (:id, :b, :score, :cat, :fin, :comp, :liq, :lev, :tr, :exp, :now)
            """),
            {
                "id": score_id,
                "b": borrower_id,
                "score": round(total_score, 1),
                "cat": category,
                "fin": round(fin_score, 1) if fin_score is not None else None,
                "comp": round(compliance_score, 1),
                "liq": round(liquidity_score, 1) if liquidity_score is not None else None,
                "lev": round(leverage_score, 1) if leverage_score is not None else None,
                "tr": round(trend_score, 1) if trend_score is not None else None,
                "exp": json.dumps(breakdown),
                "now": now,
            }
        )
        await session.commit()
        logger.info(
            "health_score.computed",
            borrower_id=borrower_id,
            score=round(total_score, 1),
            category=category,
        )

        return HealthScoreResult(total_score, category, breakdown, explanation)
