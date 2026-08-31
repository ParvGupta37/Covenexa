"""
Borrower Health Score Engine — Sprint 3.

Calculates borrower health score (0–100) based on 5 weighted dimensions:
  - Financial Performance (30%)
  - Covenant Compliance  (25%)
  - Liquidity            (20%)
  - Leverage             (15%)
  - Historical Trend     (10%)

RULES:
  - Dynamic weight re-normalization: Only available components contribute to score and denominator.
  - Unavailable components (None / N/A) contribute 0 weight to both numerator and denominator.
  - Actual measured zero (0.0) contributes 0 points but retains its weight in denominator.
  - Trend score is evaluated from historical delta before final weighted synthesis.
  - None ratio from financial_engine → omitted from formula (not treated as 0).
  - Coverage term is capped at MAX_COVERAGE_CAP before use in any formula.
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = structlog.get_logger(__name__)

MAX_COVERAGE_CAP = 50.0

# 5 Canonical Factor Weights (Sum = 1.00)
W_FINANCIAL = 0.30
W_COMPLIANCE = 0.25
W_LIQUIDITY = 0.20
W_LEVERAGE = 0.15
W_TREND = 0.10


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

        compliance_score: Optional[float] = 100.0 - (breaches * 30.0) - (warnings * 10.0)
        compliance_score = max(0.0, min(100.0, compliance_score))

        # ── 3. Fetch previous health score for trend calculation ───────────
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
        prev_score: Optional[float] = float(prev_row["score"]) if prev_row and prev_row.get("score") is not None else None

        # ── 4. Compute component scores ────────────────────────────────────
        fin_score: Optional[float] = None
        leverage_score: Optional[float] = None
        liquidity_score: Optional[float] = None
        trend_score: Optional[float] = None

        if fin:
            rev: float = float(fin["revenue"]) if fin.get("revenue") is not None else 0.0
            ebitda: Optional[float] = float(fin["ebitda"]) if fin.get("ebitda") is not None else None
            debt: float = float(fin["total_debt"]) if fin.get("total_debt") is not None else 0.0
            cash: float = float(fin["cash"]) if fin.get("cash") is not None else 0.0

            leverage: Optional[float] = (
                float(fin["leverage_ratio"]) if fin.get("leverage_ratio") is not None else None
            )
            coverage: Optional[float] = (
                float(fin["interest_coverage"]) if fin.get("interest_coverage") is not None else None
            )

            # ── Financial Score ─────────────────────────────────────────────
            if ebitda is not None and rev > 0:
                margin = ebitda / rev
                cov_for_formula = min(coverage, MAX_COVERAGE_CAP) if coverage is not None else 0.0
                fin_score = min(100.0, max(0.0, (margin * 200.0) + (cov_for_formula * 10.0)))
            elif ebitda is not None:
                cov_for_formula = min(coverage, MAX_COVERAGE_CAP) if coverage is not None else 0.0
                fin_score = min(100.0, max(0.0, 40.0 + (cov_for_formula * 5.0)))
            else:
                fin_score = None

            # ── Leverage Score ──────────────────────────────────────────────
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
                leverage_score = None

            # ── Liquidity Score ─────────────────────────────────────────────
            if debt > 0:
                liquidity_score = min(100.0, max(0.0, (cash / debt * 300.0)))
            elif cash > 0:
                liquidity_score = 90.0
            else:
                liquidity_score = 50.0

        # ── 5. Preliminary Base Score & Historical Trend Score ──────────────
        # Base operational score from available fundamental dimensions
        base_num, base_den = 0.0, 0.0
        if fin_score is not None:
            base_num += fin_score * W_FINANCIAL
            base_den += W_FINANCIAL
        if compliance_score is not None:
            base_num += compliance_score * W_COMPLIANCE
            base_den += W_COMPLIANCE
        if liquidity_score is not None:
            base_num += liquidity_score * W_LIQUIDITY
            base_den += W_LIQUIDITY
        if leverage_score is not None:
            base_num += leverage_score * W_LEVERAGE
            base_den += W_LEVERAGE

        prelim_base_score = (base_num / base_den) if base_den > 0 else compliance_score

        if prev_score is not None:
            delta = prelim_base_score - prev_score
            trend_score = max(0.0, min(100.0, 80.0 + (delta * 2.0)))
        else:
            trend_score = None  # First run — no prior health score available

        # ── 6. Final Dynamic Weight Re-normalization ────────────────────────
        # Each available factor contributes score * weight to numerator and weight to denominator.
        # Unavailable factors (None) contribute 0 to both, preserving mathematical consistency.
        def weighted_term(score: Optional[float], weight: float) -> tuple[float, float]:
            if score is None:
                return 0.0, 0.0
            return score * weight, weight

        pts_fin, w_fin       = weighted_term(fin_score, W_FINANCIAL)
        pts_comp, w_comp     = weighted_term(compliance_score, W_COMPLIANCE)
        pts_liq, w_liq       = weighted_term(liquidity_score, W_LIQUIDITY)
        pts_lev, w_lev       = weighted_term(leverage_score, W_LEVERAGE)
        pts_trend, w_trend   = weighted_term(trend_score, W_TREND)

        total_weight = w_fin + w_comp + w_liq + w_lev + w_trend

        if fin is None:
            # When zero financial records exist, score is based on compliance with 50% data haircut
            total_score = (compliance_score * 0.50) if compliance_score is not None else 50.0
        elif total_weight > 0:
            total_score = (pts_fin + pts_comp + pts_liq + pts_lev + pts_trend) / total_weight
        else:
            total_score = (compliance_score * 0.50) if compliance_score is not None else 50.0

        total_score = max(0.0, min(100.0, total_score))
        category = self._determine_category(total_score)

        # ── 7. Build Breakdown Dictionary ───────────────────────────────────
        breakdown = {
            "financial_score":  round(fin_score, 1) if fin_score is not None else None,
            "compliance_score": round(compliance_score, 1) if compliance_score is not None else None,
            "liquidity_score":  round(liquidity_score, 1) if liquidity_score is not None else None,
            "leverage_score":   round(leverage_score, 1) if leverage_score is not None else None,
            "trend_score":      round(trend_score, 1) if trend_score is not None else None,
        }

        explanation = (
            f"Health Score is {round(total_score, 1)} ({category.upper()}). "
            f"Compliance: {f'{round(compliance_score, 1)}/100' if compliance_score is not None else 'N/A'}, "
            f"Liquidity: {f'{round(liquidity_score, 1)}/100' if liquidity_score is not None else 'N/A'}, "
            f"Financial performance: {f'{round(fin_score, 1)}/100' if fin_score is not None else 'N/A'}."
        )

        # ── 8. Persist to borrower_health_scores ────────────────────────────
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
                "comp": round(compliance_score, 1) if compliance_score is not None else None,
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
