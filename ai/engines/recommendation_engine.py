"""
AI Recommendation Engine — Sprint 3 (Phase 2B: HIGH-1 fix).

Generates deterministic, actionable, non-redundant, and explainable
risk management recommendations grounded in actual covenant, health,
default risk, and financial statement data.
"""
from __future__ import annotations

import json
import uuid
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


class RecommendationEngine:
    """Generates AI-powered, data-grounded risk mitigation recommendations."""

    async def generate_recommendations(self, session, borrower_id: str) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        # 1. Fetch Borrower Info
        res_borrower = await session.execute(
            text("SELECT company_name FROM borrowers WHERE id = :b"),
            {"b": borrower_id}
        )
        borrower_row = res_borrower.mappings().first() if hasattr(res_borrower, "mappings") else None
        company_name = borrower_row.get("company_name") if borrower_row and hasattr(borrower_row, "get") else "Borrower"

        # 2. Fetch Covenant Monitoring & Facility Details
        res_cov = await session.execute(
            text("""
                SELECT cm.*, c.name as covenant_name, l.id as loan_id, l.currency, l.principal_amount
                FROM covenant_monitoring cm
                LEFT JOIN covenants c ON c.id = cm.covenant_id
                LEFT JOIN agreements a ON a.id = c.agreement_id
                LEFT JOIN loans l ON l.id = a.loan_id
                WHERE cm.borrower_id = :b
            """),
            {"b": borrower_id}
        )
        covs = res_cov.mappings().all() if hasattr(res_cov, "mappings") else []

        # 3. Fetch Latest Health Score
        res_health = await session.execute(
            text("SELECT * FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        health = res_health.mappings().first() if hasattr(res_health, "mappings") else None

        # 4. Fetch Latest Risk Assessment (Default Predictor)
        res_risk = await session.execute(
            text("SELECT * FROM risk_assessments WHERE borrower_id = :b ORDER BY assessed_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        risk = res_risk.mappings().first() if hasattr(res_risk, "mappings") else None

        # 5. Fetch Latest Financial Metrics
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first() if hasattr(res_fin, "mappings") else None

        recs: List[Dict[str, Any]] = []
        seen_types = set()

        def add_rec(rec_type: str, priority: str, title: str, reasoning: str, action_required: bool):
            clean_type = rec_type[:50]
            if clean_type in seen_types:
                return
            seen_types.add(clean_type)
            recs.append({
                "type": clean_type,
                "priority": priority,
                "title": title[:300],
                "reasoning": reasoning,
                "action_required": action_required
            })

        # ── Rule 1: Covenant Breaches & Critical Violations ────────────────────
        breaches = [c for c in covs if hasattr(c, "get") and c.get("status") in ("breach", "critical")]
        for b_cov in breaches:
            cov_name = b_cov.get("covenant_name") or b_cov.get("name") or "Covenant Maintenance"
            cov_id = b_cov.get("covenant_id") or b_cov.get("id") or str(uuid.uuid4())
            cur_val = b_cov.get("current_value")
            thr_val = b_cov.get("threshold_value")
            headroom = b_cov.get("headroom_pct")
            amt = float(b_cov.get("principal_amount") or 0)
            curr = b_cov.get("currency") or "USD"
            facility = b_cov.get("facility_name") or (f"Facility ({curr} {amt:,.0f})" if amt > 0 else "Facility")
            status_str = str(b_cov.get("status", "breach")).upper()

            cur_str = f"{cur_val:.2f}" if isinstance(cur_val, (int, float)) else "N/A"
            thr_str = f"{thr_val:.2f}" if isinstance(thr_val, (int, float)) else "N/A"
            hr_str = f"{headroom:.1f}%" if isinstance(headroom, (int, float)) else "N/A"

            title = f"Escalate Covenant Breach: {cov_name}"
            reasoning = (
                f"Issue: Covenant '{cov_name}' is in {status_str} state.\n"
                f"Evidence: Current value is {cur_str} vs. threshold of {thr_str} (Headroom: {hr_str}).\n"
                f"Related Facility/Borrower: {facility} | {company_name}.\n"
                f"Recommended Action: Immediately escalate to Senior Credit Officer and Credit Committee for waiver or breach remedy protocol."
            )
            add_rec(f"breach_{cov_id}", "urgent", title, reasoning, True)

        # ── Rule 2: Covenant Warnings ──────────────────────────────────────────
        warnings = [c for c in covs if hasattr(c, "get") and c.get("status") == "warning"]
        for w_cov in warnings:
            cov_name = w_cov.get("covenant_name") or w_cov.get("name") or "Covenant Maintenance"
            cov_id = w_cov.get("covenant_id") or w_cov.get("id") or str(uuid.uuid4())
            cur_val = w_cov.get("current_value")
            thr_val = w_cov.get("threshold_value")
            headroom = w_cov.get("headroom_pct")
            w_amt = float(w_cov.get("principal_amount") or 0)
            w_curr = w_cov.get("currency") or "USD"
            facility = w_cov.get("facility_name") or (f"Facility ({w_curr} {w_amt:,.0f})" if w_amt > 0 else "Facility")

            cur_str = f"{cur_val:.2f}" if isinstance(cur_val, (int, float)) else "N/A"
            thr_str = f"{thr_val:.2f}" if isinstance(thr_val, (int, float)) else "N/A"
            hr_str = f"{headroom:.1f}%" if isinstance(headroom, (int, float)) else "N/A"

            title = f"Increase Monitoring: {cov_name} Near Threshold"
            reasoning = (
                f"Issue: Covenant '{cov_name}' is approaching threshold limit (WARNING).\n"
                f"Evidence: Current value is {cur_str} vs. threshold of {thr_str} (Headroom: {hr_str}).\n"
                f"Related Facility/Borrower: {facility} | {company_name}.\n"
                f"Recommended Action: Increase compliance monitoring to monthly reporting cycles and request interim compliance certificate."
            )
            add_rec(f"warning_{cov_id}", "high", title, reasoning, True)

        # ── Rule 3: High Default Probability Risk ──────────────────────────────
        if risk and hasattr(risk, "get") and risk.get("default_probability") is not None:
            def_prob = float(risk["default_probability"])
            risk_cat = str(risk.get("risk_category", "high")).upper()
            if def_prob >= 20.0 or risk_cat in ("HIGH", "CRITICAL"):
                raw_factors = risk.get("risk_factors")
                if isinstance(raw_factors, str):
                    try:
                        factors_list = json.loads(raw_factors)
                    except Exception:
                        factors_list = [raw_factors]
                elif isinstance(raw_factors, list):
                    factors_list = raw_factors
                else:
                    factors_list = []

                factors_str = "; ".join(factors_list[:2]) if factors_list else "Elevated risk profile detected by credit model"
                priority = "urgent" if def_prob >= 40.0 else "high"

                title = f"Credit Watch: High Default Risk ({def_prob:.1f}%)"
                reasoning = (
                    f"Issue: High default probability identified by AI risk model.\n"
                    f"Evidence: Default Probability: {def_prob:.1f}% ({risk_cat}). Primary risk factors: {factors_str}.\n"
                    f"Related Borrower: {company_name}.\n"
                    f"Recommended Action: Place facility on Credit Watch, evaluate collateral liquidation values, and run stress scenario analysis."
                )
                add_rec("high_default_risk", priority, title, reasoning, True)

        # ── Rule 4: Low / Moderate Borrower Health Score ───────────────────────
        if health and hasattr(health, "get") and health.get("score") is not None:
            health_score = float(health["score"])
            health_cat = str(health.get("category", "moderate")).upper()
            if health_score < 60.0:
                title = f"Request Audit & Credit Review: Low Health Score ({health_score:.1f}/100)"
                reasoning = (
                    f"Issue: Borrower Health Score dropped to critical/high-risk level.\n"
                    f"Evidence: Health Score: {health_score:.1f}/100 ({health_cat}).\n"
                    f"Related Borrower: {company_name}.\n"
                    f"Recommended Action: Require updated audited quarterly financials, certified bank balance confirmations, and schedule management review."
                )
                add_rec("low_health_score", "high", title, reasoning, True)
            elif health_score < 75.0 and not breaches and not warnings:
                title = f"Evaluate Covenant Waiver / Step-Up Structure"
                reasoning = (
                    f"Issue: Moderate health score indicates tightening financial flexibility.\n"
                    f"Evidence: Health Score: {health_score:.1f}/100 ({health_cat}).\n"
                    f"Related Borrower: {company_name}.\n"
                    f"Recommended Action: Proactively evaluate step-up covenant headroom to prevent future technical breach."
                )
                add_rec("moderate_health_score", "medium", title, reasoning, False)

        # ── Rule 5: Missing / Insufficient Financial Data ──────────────────────
        has_fin = fin and hasattr(fin, "get") and (fin.get("ebitda") is not None or (fin.get("revenue") and float(fin["revenue"]) > 0))
        if not has_fin and not breaches:
            title = "Request Missing Financial Statements"
            reasoning = (
                f"Issue: Financial statements or key accounting metrics are missing.\n"
                f"Evidence: EBITDA and revenue data are unavailable for borrower '{company_name}'. Ratios cannot be calculated.\n"
                f"Related Borrower: {company_name}.\n"
                f"Recommended Action: Request certified 10-K/10-Q filing or financial statements to enable full credit risk analysis."
            )
            add_rec("missing_financial_data", "high", title, reasoning, True)

        # ── Rule 6: No Genuine Risk Issues Identified ──────────────────────────
        if not recs:
            score_val = health.get("score") if health and hasattr(health, "get") else None
            score_str = f"{float(score_val):.1f}/100" if score_val is not None else "Healthy"
            title = "No Actionable Recommendations"
            reasoning = (
                f"Issue: None identified.\n"
                f"Evidence: Borrower '{company_name}' exhibits strong health ({score_str}) with compliant covenants and low default risk.\n"
                f"Recommended Action: Maintain standard facility monitoring and routine compliance schedule."
            )
            add_rec("no_actionable_recommendations", "low", title, reasoning, False)

        # ── 6. Clear previous UNACTIONED recommendations (HIGH-2 Idempotency) ──
        await session.execute(
            text("DELETE FROM ai_recommendations WHERE borrower_id = :b AND is_actioned = FALSE"),
            {"b": borrower_id}
        )

        # ── 7. Save new recommendations to DB ─────────────────────────────────
        now = datetime.now(timezone.utc)
        saved_recs = []
        for r in recs:
            rec_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO ai_recommendations 
                    (id, borrower_id, recommendation_type, priority, title, reasoning, action_required, is_actioned, generated_at)
                    VALUES (:id, :b, :rt, :pr, :ti, :re, :ar, FALSE, :now)
                """),
                {
                    "id": rec_id,
                    "b": borrower_id,
                    "rt": r["type"],
                    "pr": r["priority"],
                    "ti": r["title"],
                    "re": r["reasoning"],
                    "ar": r["action_required"],
                    "now": now,
                }
            )
            saved_recs.append({
                "id": rec_id,
                "borrower_id": borrower_id,
                "type": r["type"],
                "priority": r["priority"],
                "title": r["title"],
                "reasoning": r["reasoning"],
                "action_required": r["action_required"],
                "is_actioned": False,
                "generated_at": now.isoformat()
            })

        await session.commit()
        logger.info("recommendation_engine.generated", borrower_id=borrower_id, count=len(saved_recs))
        return saved_recs
