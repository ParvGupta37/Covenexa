"""
Covenant Monitoring Engine — Sprint 3.
Evaluates all covenants for a borrower against latest financial metrics.
Classifies status as healthy, warning, breach, or critical.
Calculates headroom percentage and detailed reasoning.
"""
from __future__ import annotations

import uuid
import structlog
from datetime import datetime, timezone
from typing import List, Dict, Any

logger = structlog.get_logger(__name__)


class CovenantMonitor:
    """Monitors covenant compliance for borrowers."""

    async def evaluate_borrower_covenants(self, session, borrower_id: str) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        # 1. Fetch latest financial metrics
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first()

        # 2. Fetch all covenants for borrower
        res_cov = await session.execute(
            text("SELECT * FROM covenants WHERE borrower_id = :b"),
            {"b": borrower_id}
        )
        covenants = res_cov.mappings().all()

        results = []
        now = datetime.now(timezone.utc)

        for cov in covenants:
            cov_id = cov["id"]
            cov_name = cov["name"]
            cov_type = cov["covenant_type"]
            threshold = float(cov["threshold"]) if cov["threshold"] is not None else None
            direction = (cov["threshold_direction"] or "max").lower()  # max or min

            current_val = None
            status = "healthy"
            headroom_pct = 0.0
            reason = f"Covenant '{cov_name}' evaluated as healthy."
            confidence = 0.90

            if fin:
                # MEDIUM-3 (ORIGINAL-MEDIUM-1): Use the covenants.formula field as the
                # primary binding key if it is populated. Only fall back to keyword
                # heuristics when formula is NULL (older covenants extracted without
                # formula persistence).
                # RULE: None (DB NULL) = unavailable ratio — do NOT fall back to 0.0.
                formula_field = (cov.get("formula") or "").strip().lower() if hasattr(cov, "get") else ""

                # Primary: formula-based exact mapping
                if formula_field in ("leverage_ratio", "total debt / ebitda", "total net debt / ebitda", "debt/ebitda", "debt to ebitda"):
                    _raw = fin.get("leverage_ratio")
                    current_val = float(_raw) if _raw is not None else None
                elif formula_field in ("interest_coverage", "ebitda / interest expense", "ebit / interest expense"):
                    _raw = fin.get("interest_coverage")
                    current_val = float(_raw) if _raw is not None else None
                elif formula_field in ("dscr", "debt service coverage ratio"):
                    _raw = fin.get("dscr")
                    current_val = float(_raw) if _raw is not None else None
                else:
                    # Fallback: keyword heuristics on covenant name
                    name_lower = cov_name.lower()
                    if "leverage" in name_lower or "debt/ebitda" in name_lower or "debt to ebitda" in name_lower:
                        _raw = fin.get("leverage_ratio")
                        current_val = float(_raw) if _raw is not None else None
                    elif "coverage" in name_lower or "interest" in name_lower:
                        _raw = fin.get("interest_coverage")
                        current_val = float(_raw) if _raw is not None else None
                    elif "dscr" in name_lower:
                        _raw = fin.get("dscr")
                        current_val = float(_raw) if _raw is not None else None
                    elif "debt" in name_lower:
                        # total_debt is a balance-sheet item: None → 0.0 is acceptable.
                        current_val = float(fin.get("total_debt") or 0.0)
                    else:
                        _raw = fin.get("leverage_ratio")
                        current_val = float(_raw) if _raw is not None else None

            if current_val is None and threshold is not None:
                # Ratio is incalculable — mark as unknown, not healthy.
                status = "unknown"
                reason = (
                    f"Covenant '{cov_name}' could not be evaluated: "
                    f"the required financial ratio is unavailable (missing or incalculable). "
                    f"Threshold: {threshold:.2f}."
                )
                confidence = 0.0

            if threshold is not None and current_val is not None:
                if direction == "max":
                    # max limit (e.g. max leverage 4.0x)
                    headroom = threshold - current_val
                    headroom_pct = (headroom / threshold) * 100.0 if threshold > 0 else 0.0

                    if current_val > threshold:
                        status = "breach" if (current_val - threshold) < 1.0 else "critical"
                        reason = f"Breach: Current value {current_val:.2f} exceeds maximum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."
                    elif headroom_pct < 15.0:
                        status = "warning"
                        reason = f"Warning: Current value {current_val:.2f} is near maximum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."
                    else:
                        status = "healthy"
                        reason = f"Compliant: Current value {current_val:.2f} is below maximum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."
                else:
                    # min limit (e.g. min interest coverage 2.5x)
                    headroom = current_val - threshold
                    headroom_pct = (headroom / threshold) * 100.0 if threshold > 0 else 0.0

                    if current_val < threshold:
                        status = "breach" if (threshold - current_val) < 0.5 else "critical"
                        reason = f"Breach: Current value {current_val:.2f} is below minimum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."
                    elif headroom_pct < 15.0:
                        status = "warning"
                        reason = f"Warning: Current value {current_val:.2f} is near minimum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."
                    else:
                        status = "healthy"
                        reason = f"Compliant: Current value {current_val:.2f} is above minimum threshold of {threshold:.2f} (Headroom: {headroom_pct:.1f}%)."

            monitoring_id = str(uuid.uuid4())

            # Delete old monitoring entry for this covenant to maintain clean history
            await session.execute(
                text("DELETE FROM covenant_monitoring WHERE covenant_id = :cid"),
                {"cid": cov_id}
            )

            await session.execute(
                text("""
                    INSERT INTO covenant_monitoring 
                    (id, covenant_id, borrower_id, status, current_value, threshold_value, headroom_pct, reason, confidence_score, checked_at)
                    VALUES (:id, :cid, :bid, :st, :cur, :thr, :hr, :rea, :conf, :now)
                """),
                {
                    "id": monitoring_id,
                    "cid": cov_id,
                    "bid": borrower_id,
                    "st": status,
                    "cur": current_val,
                    "thr": threshold,
                    "hr": round(headroom_pct, 1),
                    "rea": reason,
                    "conf": confidence,
                    "now": now,
                }
            )

            results.append({
                "id": monitoring_id,
                "covenant_id": cov_id,
                "covenant_name": cov_name,
                "covenant_type": cov_type,
                "status": status,
                "current_value": current_val,
                "threshold_value": threshold,
                "headroom_pct": round(headroom_pct, 1),
                "reason": reason,
                "confidence_score": confidence
            })

        await session.commit()
        logger.info("covenant_monitor.evaluated", borrower_id=borrower_id, total_covenants=len(covenants))
        return results
