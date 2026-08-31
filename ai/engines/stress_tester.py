"""
Portfolio Stress Testing Engine — Sprint 3.

RULES:
  - Missing financial data → partial_data / insufficient_data, never fabricated values.
  - Distinguish None (unavailable) from 0.0 (measured zero).
  - Calculate all available stressed metrics (revenue, debt, incremental interest) even when EBITDA is None.
  - Covenant evaluation under stress: uncalculable ratios → UNKNOWN (never false compliant/resilient).
  - at_risk: True (breaches > 0), False (all covenants evaluated and passing), None (covenants UNKNOWN).
  - projected_default_prob: modeled consistently with DefaultPredictor (base + data uncertainty + stress shocks).
  - All results carry calculation_status + data_quality + caveats.
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

        caveats: List[str] = []

        # ── 3. Apply stress deltas ────────────────────────────────────────
        stressed_rev: Optional[float] = (
            round(rev_raw * (1.0 + (revenue_change_pct / 100.0)), 2) if rev_raw is not None else None
        )
        stressed_ebitda: Optional[float] = (
            round(ebitda_raw * (1.0 + (ebitda_change_pct / 100.0)), 2) if ebitda_raw is not None else None
        )
        stressed_debt: Optional[float] = (
            round(debt_raw * (1.0 + (debt_change_pct / 100.0)), 2) if debt_raw is not None else None
        )

        # Rate shock adds interest based on stressed debt notional
        interest_rate_delta = interest_rate_change_bps / 10000.0
        additional_interest = (
            stressed_debt * interest_rate_delta if stressed_debt is not None else 0.0
        )
        stressed_interest: Optional[float] = None
        if interest_raw is not None or additional_interest > 0:
            stressed_interest = round((interest_raw or 0.0) + additional_interest, 2)

        # ── 4. Stressed ratio computation (None = incalculable) ───────────
        stressed_leverage: Optional[float] = None
        if stressed_ebitda is not None and stressed_debt is not None:
            net_stressed_debt = stressed_debt - (cash_raw or 0.0)
            if abs(stressed_ebitda) >= MIN_EBITDA_FOR_LEVERAGE:
                stressed_leverage = round(net_stressed_debt / stressed_ebitda, 2)
            else:
                caveats.append(
                    f"Stressed EBITDA ({stressed_ebitda:,.0f}) is near zero — leverage ratio is undefined under this scenario."
                )
        else:
            if ebitda_raw is None:
                caveats.append("Baseline EBITDA is unavailable — stressed leverage ratio cannot be projected.")

        stressed_coverage: Optional[float] = None
        if stressed_ebitda is not None and stressed_interest is not None and stressed_interest > 0:
            raw_cov = stressed_ebitda / stressed_interest
            if raw_cov > MAX_COVERAGE_CAP:
                stressed_coverage = MAX_COVERAGE_CAP
                caveats.append(
                    f"Interest coverage ratio ({raw_cov:,.0f}x) capped at {MAX_COVERAGE_CAP}x — near-zero baseline interest detected."
                )
            else:
                stressed_coverage = round(raw_cov, 2)
        else:
            if ebitda_raw is None or interest_raw is None:
                caveats.append("Interest coverage is unavailable — missing baseline EBITDA and/or interest expense.")

        # Baseline ratios (for comparison).
        baseline_leverage: Optional[float] = None
        if ebitda_raw is not None and debt_raw is not None and abs(ebitda_raw) >= MIN_EBITDA_FOR_LEVERAGE:
            baseline_net_debt = debt_raw - (cash_raw or 0.0)
            baseline_leverage = round(baseline_net_debt / ebitda_raw, 2)

        baseline_coverage: Optional[float] = None
        if ebitda_raw is not None and interest_raw is not None and interest_raw > 0:
            raw_bl_cov = ebitda_raw / interest_raw
            baseline_coverage = min(round(raw_bl_cov, 2), MAX_COVERAGE_CAP)
            if raw_bl_cov > MAX_COVERAGE_CAP:
                caveats.append(
                    f"Baseline interest coverage ({raw_bl_cov:,.0f}x) capped at {MAX_COVERAGE_CAP}x — near-zero interest expense detected."
                )

        # ── 5. Covenant breach check under stress ─────────────────────────
        res_cov = await session.execute(
            text("""
                SELECT DISTINCT ON (c.name, COALESCE(a.loan_id, 'none'))
                    c.*, a.loan_id
                FROM covenants c
                LEFT JOIN agreements a ON c.agreement_id = a.id
                LEFT JOIN loans l ON a.loan_id = l.id
                JOIN borrowers b ON c.borrower_id = b.id
                WHERE c.borrower_id = :b
                  AND (l.is_archived IS NULL OR l.is_archived = FALSE)
                  AND b.is_archived = FALSE
                ORDER BY c.name, COALESCE(a.loan_id, 'none'), c.extracted_at DESC
            """),
            {"b": borrower_id}
        )
        covenants = res_cov.mappings().all()

        breaches = 0
        unknown_covenants = 0
        compliant_covenants = 0

        for cov in covenants:
            thresh = float(cov["threshold"]) if cov["threshold"] is not None else None
            direction = (cov["threshold_direction"] or "max").lower()
            name_lower = cov["name"].lower()

            if "leverage" in name_lower or "debt" in name_lower:
                val = stressed_leverage
            elif "coverage" in name_lower or "interest" in name_lower:
                val = stressed_coverage
            else:
                val = stressed_leverage

            if val is None:
                unknown_covenants += 1
            elif thresh is not None:
                if direction == "max" and val > thresh:
                    breaches += 1
                elif direction == "min" and val < thresh:
                    breaches += 1
                else:
                    compliant_covenants += 1

        # ── 6. Projected Default Probability under stress ─────────────────
        # Base probability (matches DefaultPredictor)
        proj_default = 5.0

        # Missing data uncertainty penalties
        if debt_raw is not None and debt_raw > 0 and ebitda_raw is None:
            proj_default += 15.0
        if interest_raw is None:
            proj_default += 10.0

        # Leverage impact
        if stressed_leverage is not None:
            if stressed_leverage > 4.5:
                proj_default += 25.0
            elif stressed_leverage > 3.5:
                proj_default += 10.0
        elif ebitda_raw is not None and ebitda_raw <= 0:
            proj_default += 30.0

        # Coverage impact
        if stressed_coverage is not None:
            if stressed_coverage < 1.5:
                proj_default += 30.0
            elif stressed_coverage < 2.5:
                proj_default += 15.0

        # Scenario shock sensitivities
        if revenue_change_pct <= -40.0:
            proj_default += 15.0
        elif revenue_change_pct <= -20.0:
            proj_default += 10.0
        elif revenue_change_pct <= -10.0:
            proj_default += 5.0

        if debt_change_pct >= 30.0:
            proj_default += 10.0
        elif debt_change_pct >= 15.0:
            proj_default += 5.0

        if interest_rate_change_bps >= 400.0:
            proj_default += 10.0
        elif interest_rate_change_bps >= 200.0:
            proj_default += 5.0

        # Covenant breaches penalty
        proj_default += (breaches * 15.0)
        proj_default = round(min(100.0, max(0.0, proj_default)), 1)

        # ── 7. Projected Health Score under stress ────────────────────────
        # Dynamic re-normalization across available stressed components
        pts_num, w_den = 0.0, 0.0

        # Compliance score under stress
        comp_score = max(0.0, 100.0 - (breaches * 30.0))
        pts_num += comp_score * 0.25
        w_den += 0.25

        # Liquidity score under stress
        if stressed_debt is not None and stressed_debt > 0 and cash_raw is not None:
            liq_score = min(100.0, max(0.0, (cash_raw / stressed_debt * 300.0)))
            pts_num += liq_score * 0.20
            w_den += 0.20
        elif cash_raw is not None and cash_raw > 0:
            pts_num += 90.0 * 0.20
            w_den += 0.20

        # Financial score under stress
        if stressed_ebitda is not None and stressed_rev is not None and stressed_rev > 0:
            margin = stressed_ebitda / stressed_rev
            cov_val = min(stressed_coverage, MAX_COVERAGE_CAP) if stressed_coverage is not None else 0.0
            fin_sc = min(100.0, max(0.0, (margin * 200.0) + (cov_val * 10.0)))
            pts_num += fin_sc * 0.30
            w_den += 0.30

        # Leverage score under stress
        if stressed_leverage is not None:
            if stressed_leverage <= 2.0:
                lev_sc = 95.0
            elif stressed_leverage <= 3.5:
                lev_sc = 80.0
            elif stressed_leverage <= 5.0:
                lev_sc = 60.0
            else:
                lev_sc = 30.0
            pts_num += lev_sc * 0.15
            w_den += 0.15

        proj_health = round(pts_num / w_den, 1) if w_den > 0 else None

        # ── 8. Determine at_risk state ────────────────────────────────────
        # True = breaches detected or extreme distress
        # False = covenants evaluated and all compliant
        # None = covenants cannot be evaluated (UNKNOWN)
        if breaches > 0:
            at_risk: Optional[bool] = True
        elif unknown_covenants > 0:
            at_risk = None  # Cannot confirm resilience when covenants are un-evaluable
            caveats.append(
                f"{unknown_covenants} covenant(s) could not be evaluated under stress due to unavailable ratios."
            )
        elif len(covenants) == 0:
            at_risk = None
        else:
            at_risk = False

        # ── 9. Determine calculation_status ───────────────────────────────
        missing_count = sum([
            ebitda_raw is None,
            interest_raw is None,
            rev_raw is None,
            debt_raw is None,
        ])
        if missing_count == 0:
            calculation_status = "valid"
        else:
            calculation_status = "partial_data"

        # ── 10. Build data_quality summary ────────────────────────────────
        data_quality = {
            "ebitda_available": ebitda_raw is not None,
            "revenue_available": rev_raw is not None,
            "debt_available": debt_raw is not None,
            "interest_available": interest_raw is not None and interest_raw > 0,
            "leverage_calculable": stressed_leverage is not None,
            "coverage_calculable": stressed_coverage is not None,
        }

        # ── 11. Persist result ────────────────────────────────────────────
        now = datetime.now(timezone.utc)
        result_id = str(uuid.uuid4())

        res_json = {
            "baseline": {
                "revenue": rev_raw,
                "debt": debt_raw,
                "leverage": baseline_leverage,
                "coverage": baseline_coverage,
            },
            "stressed": {
                "revenue": stressed_rev,
                "ebitda": stressed_ebitda,
                "debt": stressed_debt,
                "interest": stressed_interest,
                "leverage": stressed_leverage,
                "coverage": stressed_coverage,
            },
            "deltas": {
                "revenue_pct": revenue_change_pct,
                "ebitda_pct": ebitda_change_pct,
                "rate_bps": interest_rate_change_bps,
                "debt_pct": debt_change_pct,
            },
            "covenants_summary": {
                "total": len(covenants),
                "breaches": breaches,
                "unknown": unknown_covenants,
                "compliant": compliant_covenants,
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
                "ar": bool(at_risk) if at_risk is not None else False,
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
        """Return a structured response when zero financial data exists."""
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
            "details": {
                "baseline": {"revenue": None, "debt": None, "leverage": None, "coverage": None},
                "stressed": {"revenue": None, "ebitda": None, "debt": None, "interest": None, "leverage": None, "coverage": None},
                "covenants_summary": {"total": 0, "breaches": 0, "unknown": 0, "compliant": 0},
            },
        }

