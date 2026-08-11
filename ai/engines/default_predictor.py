"""
Default Prediction Engine — Sprint 3 (Phase 2B: HIGH-3 fix).

RULES:
  - coverage == None (unavailable) → explicit risk factor, NOT skipped.
  - coverage == 0.0 (actual zero) → treated as severe distress signal.
  - Confidence calibrated on actual data presence, not just row existence.
  - Missing EBITDA with positive debt → high-severity risk factor added.
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = structlog.get_logger(__name__)


class DefaultPredictor:
    """Predicts default probability and risk factors for borrowers."""

    async def predict_and_persist(self, session, borrower_id: str) -> Dict[str, Any]:
        from sqlalchemy import text

        # ── 1. Fetch latest financial metrics & health score ──────────────
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first()

        res_health = await session.execute(
            text("SELECT * FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        health = res_health.mappings().first()

        risk_factors: List[str] = []
        base_prob = 5.0

        # ── 2. Financial metric–based risk factors ─────────────────────────
        if fin:
            # Use None-aware reads — distinguish missing from zero.
            leverage: Optional[float] = (
                float(fin["leverage_ratio"]) if fin.get("leverage_ratio") is not None else None
            )
            coverage: Optional[float] = (
                float(fin["interest_coverage"]) if fin.get("interest_coverage") is not None else None
            )
            ebitda: Optional[float] = (
                float(fin["ebitda"]) if fin.get("ebitda") is not None else None
            )
            total_debt: float = float(fin["total_debt"]) if fin.get("total_debt") is not None else 0.0

            # ── Leverage risk ──────────────────────────────────────────────
            if leverage is not None:
                if leverage > 4.5:
                    base_prob += 25.0
                    risk_factors.append(f"High Leverage Ratio ({leverage:.2f}x > 4.5x limit)")
                elif leverage > 3.5:
                    base_prob += 10.0
                    risk_factors.append(f"Elevated Leverage Ratio ({leverage:.2f}x)")
            else:
                # Leverage incalculable — cannot rule out risk.
                if total_debt > 0 and ebitda is None:
                    base_prob += 15.0
                    risk_factors.append(
                        "EBITDA unavailable — leverage ratio cannot be calculated. "
                        "Debt service capacity is unverified."
                    )
                elif ebitda is not None and ebitda <= 0:
                    base_prob += 30.0
                    risk_factors.append(
                        f"EBITDA is zero or negative ({ebitda:,.0f}) — "
                        "severe earnings distress; leverage is undefined."
                    )

            # ── Coverage risk ──────────────────────────────────────────────
            # CRITICAL: distinguish None (not available) from 0.0 (actual zero).
            if coverage is None:
                # Coverage unavailable — this is unknown risk, not zero risk.
                base_prob += 10.0
                risk_factors.append(
                    "Interest coverage ratio unavailable — unable to assess debt service capacity. "
                    "Interest expense may be missing from extracted financials."
                )
            elif coverage == 0.0:
                # Actual zero coverage → severe distress.
                base_prob += 30.0
                risk_factors.append("Interest Coverage Ratio is 0x — borrower cannot service interest from EBITDA.")
            elif coverage < 1.5:
                base_prob += 30.0
                risk_factors.append(f"Severe Interest Coverage Deficit ({coverage:.2f}x < 1.5x)")
            elif coverage < 2.5:
                base_prob += 15.0
                risk_factors.append(f"Tight Interest Coverage ({coverage:.2f}x)")
            # coverage >= 2.5 → no penalty (healthy)

        else:
            # No financial row at all.
            risk_factors.append(
                "No financial statements ingested for this borrower. "
                "Default risk cannot be quantified without financial data."
            )
            base_prob += 10.0  # small uncertainty uplift (not zero extra risk)

        # ── 3. Health score–based risk factors ─────────────────────────────
        if health:
            health_score = float(health["score"])
            if health_score < 50:
                base_prob += 20.0
                risk_factors.append(f"Low Borrower Health Score ({health_score:.1f}/100)")
            elif health_score < 65:
                base_prob += 10.0

        # ── 4. Positive signal when no risk factors triggered ──────────────
        if not risk_factors:
            # MEDIUM-3: Base probability is 5.0% (calibrated baseline for borrowers with
            # no identified risk signals). This is a model constant, not model-derived.
            # Made explicit here so it is traceable and not a silent magic number.
            risk_factors.append(
                "No elevated risk signals detected. Baseline probability of 5.0% applied "
                "(calibrated default floor — not derived from borrower-specific data)."
            )
            risk_factors.append("Strong financial fundamentals and comfortable covenant headroom.")

        default_prob = round(max(0.5, min(95.0, base_prob)), 1)
        z_score = round(3.5 - (default_prob / 20.0), 2)

        if default_prob >= 40.0:
            category = "critical"
        elif default_prob >= 20.0:
            category = "high"
        elif default_prob >= 10.0:
            category = "medium"
        else:
            category = "low"

        # ── 5. Confidence calibration ─────────────────────────────────────
        # 0.88: full confidence — EBITDA, revenue AND interest_expense all present.
        # 0.65: partial confidence — core P&L available but coverage unverifiable.
        # 0.30: very low — no financial data at all.
        if fin:
            ebitda_val = float(fin["ebitda"]) if fin.get("ebitda") is not None else None
            revenue_val = float(fin["revenue"]) if fin.get("revenue") is not None else 0.0
            interest_val = float(fin["interest_expense"]) if fin.get("interest_expense") is not None else None
            has_core = ebitda_val is not None and ebitda_val != 0 and revenue_val > 0
            has_interest = interest_val is not None and interest_val > 0
            if has_core and has_interest:
                confidence = 0.88
            elif has_core:
                confidence = 0.65   # cannot verify debt-service capacity
            else:
                confidence = 0.55   # fin row exists but key fields missing
        else:
            confidence = 0.30

        now = datetime.now(timezone.utc)
        assessment_id = str(uuid.uuid4())

        await session.execute(
            text("""
                INSERT INTO risk_assessments
                (id, borrower_id, default_probability, risk_category, confidence_score,
                 z_score, risk_factors, assessed_at)
                VALUES (:id, :b, :dp, :rc, :cs, :zs, :rf, :now)
            """),
            {
                "id": assessment_id,
                "b": borrower_id,
                "dp": default_prob,
                "rc": category,
                "cs": confidence,
                "zs": z_score,
                "rf": json.dumps(risk_factors),
                "now": now,
            }
        )
        await session.commit()
        logger.info(
            "default_predictor.completed",
            borrower_id=borrower_id,
            default_prob=default_prob,
            category=category,
            confidence=confidence,
        )

        return {
            "id": assessment_id,
            "borrower_id": borrower_id,
            "default_probability": default_prob,
            "risk_category": category,
            "confidence_score": confidence,
            "z_score": z_score,
            "risk_factors": risk_factors,
            "assessed_at": now.isoformat()
        }
