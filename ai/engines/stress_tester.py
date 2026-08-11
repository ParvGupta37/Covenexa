"""
Portfolio Stress Testing Engine — Sprint 3 (Phase 2B: HIGH-3 fix).

RULES:
  - Missing financial data → INSUFFICIENT_DATA, not 0% default.
  - Near-zero / undefined ratios → capped/None, not injected into formula.
  - All results carry calculation_status + data_quality + caveats.
  - proj_health formula is bounded and does not let any single ratio
    dominate (coverage capped at MAX_COVERAGE_CAP before use).
"""
from __future__ import annotations

import uuid
import json
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = structlog.get_logger(__name__)

MAX_COVERAGE_CAP = 50.0   # x coverage beyond this is an artefact of near-zero interest
MIN_EBITDA_FOR_LEVERAGE = 1.0   # absolute floor below which leverage is incalculable


class StressTester:
    """Runs stress test scenario simulations across borrowers using actual extracted data."""

    async def run_scenario(
        self,
        session,
        borrower_id: str,
        scenario_name: str,
        revenue_change_pct: float = 0.0,
        ebitda_change_pct: float = 0.0,
        interest_rate_change_bps: float = 0.0,
        debt_change_pct: float = 0.0
    ) -> Dict[str, Any]:
        from sqlalchemy import text

        # ── 1. Fetch current financial metrics ────────────────────────────
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first()

        if not fin:
            return self._insufficient_data_response(
                borrower_id=borrower_id,
                scenario_name=scenario_name,
                reason="No financial metrics found for this borrower. Upload and process a financial document first."
            )

        # ── 2. Extract raw baseline values ────────────────────────────────
        # Distinguish None (not reported) from 0.0 (actually zero).
        rev_raw: Optional[float] = float(fin["revenue"]) if fin.get("revenue") is not None else None
        ebitda_raw: Optional[float] = float(fin["ebitda"]) if fin.get("ebitda") is not None else None
        debt_raw: Optional[float] = float(fin["total_debt"]) if fin.get("total_debt") is not None else None
        cash_raw: Optional[float] = float(fin["cash"]) if fin.get("cash") is not None else None
        interest_raw: Optional[float] = (
            float(fin["interest_expense"]) if fin.get("interest_expense") is not None else None
        )

        # Need at least EBITDA to run any meaningful stress calculation.
        if ebitda_raw is None:
            return self._insufficient_data_response(
                borrower_id=borrower_id,
                scenario_name=scenario_name,
                reason="EBITDA is unavailable. Cannot calculate leverage or project health under stress."
            )

        # Convenience fallbacks for non-critical fields (zero is valid here).
        rev = rev_raw if rev_raw is not None else 0.0
        debt = debt_raw if debt_raw is not None else 0.0
        cash = cash_raw if cash_raw is not None else 0.0
        interest = interest_raw if interest_raw is not None else 0.0

        # ── 3. Apply stress deltas ────────────────────────────────────────
        stressed_rev = rev * (1.0 + (revenue_change_pct / 100.0))
        stressed_ebitda = ebitda_raw * (1.0 + (ebitda_change_pct / 100.0))
        stressed_debt = debt * (1.0 + (debt_change_pct / 100.0))

        # Rate shock adds interest based on stressed debt notional.
        interest_rate_delta = interest_rate_change_bps / 10000.0
        additional_interest = stressed_debt * interest_rate_delta
        stressed_interest = interest + additional_interest

        # ── 4. Stressed ratio computation (None = incalculable) ───────────
        caveats: List[str] = []
        net_stressed_debt = stressed_debt - cash

        stressed_leverage: Optional[float] = None
        if abs(stressed_ebitda) >= MIN_EBITDA_FOR_LEVERAGE:
            stressed_leverage = round(net_stressed_debt / stressed_ebitda, 2)
        else:
            caveats.append(
                f"Stressed EBITDA ({stressed_ebitda:,.0f}) is near zero — "
                "leverage ratio is undefined under this scenario."
            )

        stressed_coverage: Optional[float] = None
        if stressed_interest > 0:
            raw_cov = stressed_ebitda / stressed_interest
            if raw_cov > MAX_COVERAGE_CAP:
                stressed_coverage = MAX_COVERAGE_CAP
                caveats.append(
                    f"Interest coverage ratio ({raw_cov:,.0f}x) capped at {MAX_COVERAGE_CAP}x "
                    "— near-zero interest expense detected. Baseline interest expense may be "
                    "understated (possible SEC unit mismatch). Rate shock adds meaningful "
                    f"interest ({additional_interest:,.0f})."
                )
            else:
                stressed_coverage = round(raw_cov, 2)
        elif additional_interest > 0:
            # Borrower had near-zero base interest but rate shock creates real cost.
            stressed_coverage = round(stressed_ebitda / additional_interest, 2)
            caveats.append(
                "Baseline interest expense was zero/negligible; coverage calculated "
                "using rate-shock-induced interest expense only."
            )
        else:
            caveats.append(
                "Interest coverage is undefined: no baseline interest expense "
                "and no rate shock applied."
            )

        # Baseline ratios (for comparison).
        baseline_leverage: Optional[float] = None
        if abs(ebitda_raw) >= MIN_EBITDA_FOR_LEVERAGE:
            baseline_net_debt = debt - cash
            baseline_leverage = round(baseline_net_debt / ebitda_raw, 2)

        baseline_coverage: Optional[float] = None
        if interest > 0:
            raw_bl_cov = ebitda_raw / interest
            baseline_coverage = min(round(raw_bl_cov, 2), MAX_COVERAGE_CAP)
            if raw_bl_cov > MAX_COVERAGE_CAP:
                caveats.append(
                    f"Baseline interest coverage ({raw_bl_cov:,.0f}x) capped at "
                    f"{MAX_COVERAGE_CAP}x for formula use."
                )

        # ── 5. Covenant breach check under stress ─────────────────────────
        res_cov = await session.execute(
            text("SELECT * FROM covenants WHERE borrower_id = :b"),
            {"b": borrower_id}
        )
        covenants = res_cov.mappings().all()

        breaches = 0
        for cov in covenants:
            thresh = float(cov["threshold"]) if cov["threshold"] is not None else None
            direction = (cov["threshold_direction"] or "max").lower()
            name_lower = cov["name"].lower()

            # Only evaluate covenant if the relevant ratio is calculable.
            if "leverage" in name_lower or "debt" in name_lower:
                val = stressed_leverage
            elif "coverage" in name_lower or "interest" in name_lower:
                val = stressed_coverage
            else:
                val = stressed_leverage  # default to leverage

            if thresh is not None and val is not None:
                if direction == "max" and val > thresh:
                    breaches += 1
                elif direction == "min" and val < thresh:
                    breaches += 1

        # ── 6. Projected health score — bounded, component-based ──────────
        # Base: neutral 60. Never starts optimistic.
        base_health = 60.0

        # EBITDA margin contribution (bounded ±20 pts).
        if stressed_rev > 0 and stressed_ebitda is not None:
            margin = stressed_ebitda / stressed_rev
            margin_pts = max(-20.0, min(20.0, margin * 100.0))
        else:
            margin_pts = 0.0

        # Leverage penalty/bonus (capped contribution ±15 pts).
        if stressed_leverage is not None:
            if stressed_leverage <= 2.0:
                leverage_pts = 15.0
            elif stressed_leverage <= 3.5:
                leverage_pts = 5.0
            elif stressed_leverage <= 5.0:
                leverage_pts = -10.0
            else:
                leverage_pts = -15.0
        else:
            # Undefined leverage → uncertainty penalty (not zero penalty).
            leverage_pts = -5.0
            caveats.append("Leverage ratio undefined under stress — applying uncertainty discount.")

        # Coverage contribution (capped at ±10 pts; uses already-capped ratio).
        if stressed_coverage is not None:
            if stressed_coverage >= 3.0:
                coverage_pts = 10.0
            elif stressed_coverage >= 1.5:
                coverage_pts = 2.0
            elif stressed_coverage >= 0.5:
                coverage_pts = -5.0
            else:
                coverage_pts = -10.0
        else:
            coverage_pts = -3.0  # uncertainty penalty, not zero
            caveats.append("Interest coverage ratio unavailable under stress — applying uncertainty discount.")

        # Breach penalty.
        breach_pts = -(breaches * 15.0)

        proj_health = round(
            max(0.0, min(100.0, base_health + margin_pts + leverage_pts + coverage_pts + breach_pts)),
            1
        )
        proj_default = round(min(100.0, max(0.0, (100.0 - proj_health) * 0.8)), 1)
        at_risk = (breaches > 0 or proj_health < 50.0 or proj_default > 25.0)

        # ── 7. Determine calculation_status ──────────────────────────────
        missing_count = sum([
            ebitda_raw is None,
            interest_raw is None,
            rev_raw is None,
            debt_raw is None,
        ])
        if missing_count == 0 and not caveats:
            calculation_status = "valid"
        elif missing_count > 0:
            calculation_status = "partial_data"
        else:
            calculation_status = "partial_data"

        # ── 8. Build data_quality summary ─────────────────────────────────
        data_quality = {
            "ebitda_available": ebitda_raw is not None,
            "revenue_available": rev_raw is not None,
            "debt_available": debt_raw is not None,
            "interest_available": interest_raw is not None and interest_raw > 0,
            "leverage_calculable": stressed_leverage is not None,
            "coverage_calculable": stressed_coverage is not None,
        }

        # ── 9. Persist result ─────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        result_id = str(uuid.uuid4())

        res_json = {
            "baseline": {
                "leverage": baseline_leverage,
                "coverage": baseline_coverage,
            },
            "stressed": {
                "revenue": stressed_rev,
                "ebitda": stressed_ebitda,
                "debt": stressed_debt,
                "leverage": stressed_leverage,
                "coverage": stressed_coverage,
            },
            "deltas": {
                "revenue_pct": revenue_change_pct,
                "ebitda_pct": ebitda_change_pct,
                "rate_bps": interest_rate_change_bps,
                "debt_pct": debt_change_pct,
            },
            "calculation_status": calculation_status,
            "data_quality": data_quality,
            "caveats": caveats,
        }

        await session.execute(
            text("""
                INSERT INTO stress_test_results
                (id, borrower_id, scenario_name, revenue_change_pct, ebitda_change_pct,
                 interest_rate_change_bps, debt_change_pct, projected_health_score,
                 projected_default_prob, covenant_breaches_count, at_risk, results_json, run_at)
                VALUES (:id, :b, :sn, :rev, :eb, :ir, :d, :phs, :pdp, :cbc, :ar, :rj, :now)
            """),
            {
                "id": result_id,
                "b": borrower_id,
                "sn": scenario_name,
                "rev": revenue_change_pct,
                "eb": ebitda_change_pct,
                "ir": interest_rate_change_bps,
                "d": debt_change_pct,
                "phs": proj_health,
                "pdp": proj_default,
                "cbc": breaches,
                "ar": at_risk,
                "rj": json.dumps(res_json),
                "now": now,
            }
        )
        await session.commit()
        logger.info(
            "stress_tester.scenario_run",
            borrower_id=borrower_id,
            scenario=scenario_name,
            at_risk=at_risk,
            calculation_status=calculation_status,
            caveats=caveats,
        )

        return {
            "id": result_id,
            "borrower_id": borrower_id,
            "scenario_name": scenario_name,
            "projected_health_score": proj_health,
            "projected_default_prob": proj_default,
            "covenant_breaches_count": breaches,
            "at_risk": at_risk,
            "calculation_status": calculation_status,
            "data_quality": data_quality,
            "caveats": caveats,
            "details": res_json,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _insufficient_data_response(
        self,
        borrower_id: str,
        scenario_name: str,
        reason: str,
    ) -> Dict[str, Any]:
        """Return a structured response when data is insufficient to run stress test."""
        logger.warning(
            "stress_tester.insufficient_data",
            borrower_id=borrower_id,
            reason=reason,
        )
        return {
            "id": None,
            "borrower_id": borrower_id,
            "scenario_name": scenario_name,
            "projected_health_score": None,
            "projected_default_prob": None,
            "covenant_breaches_count": 0,
            "at_risk": None,
            "calculation_status": "insufficient_data",
            "data_quality": {
                "ebitda_available": False,
                "revenue_available": False,
                "debt_available": False,
                "interest_available": False,
                "leverage_calculable": False,
                "coverage_calculable": False,
            },
            "caveats": [reason],
            "details": {},
        }
