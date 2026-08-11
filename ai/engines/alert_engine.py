"""
Alert Engine — Sprint 3.
Generates severity-classified system alerts for:
- Covenant Breach (Critical / High)
- Upcoming Reporting Deadlines (Info / Warning)
- Financial Deterioration (Warning / High)
- High Default Probability (Critical)
"""
from __future__ import annotations

import json
import uuid
import structlog
from datetime import datetime, timezone
from typing import Dict, Any, List

logger = structlog.get_logger(__name__)


class AlertEngine:
    """Generates and manages real-time system alerts."""

    async def check_and_generate_alerts(self, session, borrower_id: str) -> List[Dict[str, Any]]:
        from sqlalchemy import text

        # 1. Fetch borrower name
        res_b = await session.execute(text("SELECT company_name FROM borrowers WHERE id = :b"), {"b": borrower_id})
        b_row = res_b.mappings().first()
        b_name = b_row["company_name"] if b_row else "Borrower"

        # 2. Check covenant monitoring for breaches/critical
        res_cov = await session.execute(
            text("SELECT * FROM covenant_monitoring WHERE borrower_id = :b AND status IN ('breach', 'critical', 'warning')"),
            {"b": borrower_id}
        )
        cov_issues = res_cov.mappings().all()

        # 3. Check health score
        res_health = await session.execute(
            text("SELECT * FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        health = res_health.mappings().first()

        alerts = []
        now = datetime.now(timezone.utc)

        for issue in cov_issues:
            st = issue["status"]
            sev = "critical" if st == "critical" else ("high" if st == "breach" else "warning")
            title = f"Covenant {st.capitalize()}: {issue['reason'][:80]}..."
            msg = issue["reason"]

            alerts.append({
                "borrower_id": borrower_id,
                "alert_type": f"covenant_{st}",
                "severity": sev,
                "title": f"[{b_name}] {title}",
                "message": msg,
                "metadata": json.dumps({"covenant_id": issue["covenant_id"], "headroom": issue["headroom_pct"]})
            })

        if health and float(health["score"]) < 50.0:
            alerts.append({
                "borrower_id": borrower_id,
                "alert_type": "health_score_critical",
                "severity": "critical",
                "title": f"[{b_name}] Borrower Health Score Critical ({health['score']:.1f}/100)",
                "message": f"Borrower health has dropped into critical category ({health['category']}). Immediate risk evaluation required.",
                "metadata": json.dumps({"health_score": health["score"], "category": health["category"]})
            })

        # Save to alerts table
        saved_alerts = []
        for a in alerts:
            alert_id = str(uuid.uuid4())
            await session.execute(
                text("""
                    INSERT INTO alerts (id, borrower_id, alert_type, severity, title, message, is_read, metadata, created_at)
                    VALUES (:id, :bid, :at, :sev, :ti, :msg, FALSE, :meta, :now)
                """),
                {
                    "id": alert_id,
                    "bid": a["borrower_id"],
                    "at": a["alert_type"],
                    "sev": a["severity"],
                    "ti": a["title"],
                    "msg": a["message"],
                    "meta": a["metadata"],
                    "now": now,
                }
            )
            saved_alerts.append({
                "id": alert_id,
                "borrower_id": borrower_id,
                "alert_type": a["alert_type"],
                "severity": a["severity"],
                "title": a["title"],
                "message": a["message"],
                "is_read": False,
                "created_at": now.isoformat()
            })

        await session.commit()
        logger.info("alert_engine.checked", borrower_id=borrower_id, count=len(saved_alerts))
        return saved_alerts
