"""
Risk Engine API Endpoints — Sprint 3.
Provides endpoints for:
- GET  /risk/health/{borrower_id}
- GET  /risk/portfolio
- GET  /risk/default/{borrower_id}
- GET  /risk/covenants/{borrower_id}
- POST /risk/stress
- GET  /risk/recommendations/{borrower_id}
- POST /risk/pipeline/{borrower_id}
- GET  /risk/trend
- GET  /risk/distribution
- GET  /risk/graph/{borrower_id}
"""
import re
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role, get_current_user
from app.domain.entities.user import User, UserRole
from ai.engines.pipeline_runner import RiskIntelligencePipeline
from ai.engines.stress_tester import StressTester

router = APIRouter(prefix="/risk", tags=["Risk Intelligence"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


class StressTestRequest(BaseModel):
    borrower_id: str
    scenario_name: str = "Recession Simulation"
    revenue_change_pct: float = -15.0
    ebitda_change_pct: float = -20.0
    interest_rate_change_bps: float = 200.0
    debt_change_pct: float = 10.0


# ── GET /risk/health/{borrower_id} ─────────────────────────────────────────────
@router.get("/health/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_borrower_health(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Returns latest borrower health score & historical score trend from database."""
    result = await session.execute(
        text("SELECT * FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
        {"b": borrower_id}
    )
    latest = result.mappings().first()

    if not latest:
        # RULE: None = unavailable; 0 = actual calculated zero.
        # Never return 0 for a score that was never calculated.
        return {
            "score": None,
            "category": "NO DATA",
            "explanation": "No financial documents or covenants ingested yet.",
            "breakdown": {
                "financial_score": None,
                "compliance_score": None,
                "liquidity_score": None,
                "leverage_score": None,
                "trend_score": None,
            },
            "history": [],
            "calculated_at": None
        }

    import json
    history_res = await session.execute(
        text("SELECT score, category, calculated_at FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at ASC LIMIT 10"),
        {"b": borrower_id}
    )
    history = [dict(r) for r in history_res.mappings().all()]

    explanation_obj = {}
    if latest["explanation"]:
        try:
            explanation_obj = json.loads(latest["explanation"])
        except Exception:
            explanation_obj = {}

    return {
        "score": latest["score"],
        "category": latest["category"],
        "explanation": latest["explanation"],
        "breakdown": {
            # Null-preserving: only fall back to JSON explanation if DB column is None.
            # Never substitute 0 for a column that is legitimately NULL.
            "financial_score": latest["financial_score"] if latest["financial_score"] is not None else explanation_obj.get("financial_score"),
            "compliance_score": latest["compliance_score"] if latest["compliance_score"] is not None else explanation_obj.get("compliance_score"),
            "liquidity_score": latest["liquidity_score"] if latest["liquidity_score"] is not None else explanation_obj.get("liquidity_score"),
            "leverage_score": latest["leverage_score"] if latest["leverage_score"] is not None else explanation_obj.get("leverage_score"),
            "trend_score": latest["trend_score"] if latest["trend_score"] is not None else explanation_obj.get("trend_score"),
        },
        "history": history,
        "calculated_at": latest["calculated_at"].isoformat() if latest["calculated_at"] else None
    }


# ── GET /risk/portfolio ────────────────────────────────────────────────────────
@router.get("/portfolio", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_portfolio_risk_summary(session: AsyncSession = Depends(get_db_session)) -> Dict[str, Any]:
    """Aggregates portfolio-wide risk metrics strictly from calculated database entries."""
    res_b = await session.execute(text("SELECT COUNT(*) FROM borrowers WHERE is_archived = FALSE"))
    total_borrowers = res_b.scalar() or 0

    res_scores = await session.execute(
        text("""
            SELECT DISTINCT ON (bhs.borrower_id) bhs.score, bhs.category 
            FROM borrower_health_scores bhs
            JOIN borrowers b ON bhs.borrower_id = b.id
            WHERE b.is_archived = FALSE
            ORDER BY bhs.borrower_id, bhs.calculated_at DESC
        """)
    )
    scores_rows = res_scores.mappings().all()
    scores = [r["score"] for r in scores_rows]

    if scores:
        avg_score = round(sum(scores) / len(scores), 1)
        portfolio_risk_score = round(max(0.0, 100.0 - avg_score), 1)
    else:
        # MEDIUM-3 (NEW-3): No health scores calculated yet.
        # None = data unavailable, not a risk score of 0.
        # 0.0 would imply the portfolio is risk-free (or at max risk), which is false.
        avg_score = None
        portfolio_risk_score = None

    portfolio_risk_level = (
        "LOW" if (portfolio_risk_score is not None and portfolio_risk_score < 30)
        else ("MEDIUM" if (portfolio_risk_score is not None and portfolio_risk_score < 60)
              else ("HIGH" if portfolio_risk_score is not None else "NO DATA"))
    )

    res_breaches = await session.execute(
        text("""
            SELECT COUNT(*) FROM covenant_monitoring cm
            JOIN covenants c ON cm.covenant_id = c.id
            JOIN borrowers b ON c.borrower_id = b.id
            WHERE cm.status IN ('breach', 'critical') AND b.is_archived = FALSE
        """)
    )
    active_breaches = res_breaches.scalar() or 0

    res_alerts = await session.execute(
        text("""
            SELECT COUNT(*) FROM alerts a
            JOIN borrowers b ON a.borrower_id = b.id
            WHERE a.is_read = FALSE AND b.is_archived = FALSE
        """)
    )
    active_alerts = res_alerts.scalar() or 0

    res_high_risk = await session.execute(
        text("""
            SELECT COUNT(DISTINCT bhs.borrower_id) 
            FROM borrower_health_scores bhs
            JOIN borrowers b ON bhs.borrower_id = b.id
            WHERE bhs.category IN ('high_risk', 'critical') AND b.is_archived = FALSE
        """)
    )
    high_risk_count = res_high_risk.scalar() or 0

    return {
        "portfolio_risk_score": portfolio_risk_score,
        "portfolio_risk_level": portfolio_risk_level,
        "average_borrower_score": avg_score,
        "total_borrowers": total_borrowers,
        "high_risk_borrowers": high_risk_count,
        "active_covenant_breaches": active_breaches,
        "active_alerts": active_alerts,
    }


# ── GET /risk/trend ────────────────────────────────────────────────────────────
@router.get("/trend", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_portfolio_health_trend(session: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Returns actual historical borrower health scores timeline from DB."""
    result = await session.execute(
        text("""
            SELECT TO_CHAR(calculated_at, 'Mon DD') as date_label,
                   ROUND(AVG(score)::numeric, 1) as score
            FROM borrower_health_scores
            GROUP BY TO_CHAR(calculated_at, 'Mon DD'), DATE(calculated_at)
            ORDER BY DATE(calculated_at) ASC
            LIMIT 12
        """)
    )
    rows = result.mappings().all()
    return [{"month": r["date_label"], "score": float(r["score"])} for r in rows]


# ── GET /risk/distribution ─────────────────────────────────────────────────────
@router.get("/distribution", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_risk_distribution(session: AsyncSession = Depends(get_db_session)) -> List[Dict[str, Any]]:
    """Returns actual borrower distribution across health tiers from DB."""
    result = await session.execute(
        text("""
            WITH latest_scores AS (
                SELECT DISTINCT ON (bhs.borrower_id) bhs.category
                FROM borrower_health_scores bhs
                JOIN borrowers b ON bhs.borrower_id = b.id
                WHERE b.is_archived = FALSE
                ORDER BY bhs.borrower_id, bhs.calculated_at DESC
            )
            SELECT category, COUNT(*) as cnt
            FROM latest_scores
            GROUP BY category
        """)
    )
    rows = result.mappings().all()
    cat_counts = {r["category"]: r["cnt"] for r in rows}

    categories = [
        ("Excellent (90-100)", "excellent"),
        ("Good (75-89)", "good"),
        ("Moderate (60-74)", "moderate"),
        ("High Risk (<60)", "high_risk"),
        ("Critical (<40)", "critical"),
    ]

    return [{"name": name, "value": cat_counts.get(key, 0)} for name, key in categories]


# ── GET /risk/default/{borrower_id} ────────────────────────────────────────────
@router.get("/default/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_default_prediction(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Returns default probability & risk factors."""
    result = await session.execute(
        text("SELECT * FROM risk_assessments WHERE borrower_id = :b ORDER BY assessed_at DESC LIMIT 1"),
        {"b": borrower_id}
    )
    row = result.mappings().first()

    if not row:
        # RULE: None = unavailable; 0.0 = actual zero risk (calculated).
        # An unanalyzed borrower must NOT appear as 0% default probability.
        return {
            "default_probability": None,
            "risk_category": "NO DATA",
            "confidence_score": None,
            "z_score": None,
            "risk_factors": ["No financial data uploaded yet for this entity."],
            "assessed_at": None
        }

    import json
    return {
        "default_probability": row["default_probability"],
        "risk_category": row["risk_category"],
        "confidence_score": row["confidence_score"],
        "z_score": row["z_score"],
        "risk_factors": json.loads(row["risk_factors"]) if row["risk_factors"] else [],
        "assessed_at": row["assessed_at"].isoformat() if row["assessed_at"] else None
    }


# ── GET /risk/covenants/{borrower_id} ──────────────────────────────────────────
@router.get("/covenants/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_monitored_covenants(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Returns evaluated covenant compliance statuses with headroom and reasons for active loans."""
    result = await session.execute(
        text("""
            SELECT DISTINCT ON (c.name, COALESCE(a.loan_id, 'none'))
                cm.*, c.name as covenant_name, c.covenant_type, c.raw_text, a.loan_id
            FROM covenant_monitoring cm
            JOIN covenants c ON cm.covenant_id = c.id
            LEFT JOIN agreements a ON c.agreement_id = a.id
            LEFT JOIN loans l ON a.loan_id = l.id
            JOIN borrowers b ON cm.borrower_id = b.id
            WHERE cm.borrower_id = :b
              AND (l.is_archived IS NULL OR l.is_archived = FALSE)
              AND b.is_archived = FALSE
            ORDER BY c.name, COALESCE(a.loan_id, 'none'), cm.checked_at DESC
        """),
        {"b": borrower_id}
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


# ── POST /risk/stress ──────────────────────────────────────────────────────────
@router.post("/stress", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def run_stress_test(
    req: StressTestRequest,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Runs interactive stress test scenario for a borrower."""
    tester = StressTester()
    res = await tester.run_scenario(
        session,
        borrower_id=req.borrower_id,
        scenario_name=req.scenario_name,
        revenue_change_pct=req.revenue_change_pct,
        ebitda_change_pct=req.ebitda_change_pct,
        interest_rate_change_bps=req.interest_rate_change_bps,
        debt_change_pct=req.debt_change_pct,
    )
    return res


# ── GET /risk/recommendations/{borrower_id} ────────────────────────────────────
@router.get("/recommendations/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_ai_recommendations(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Returns AI-generated risk management recommendations."""
    result = await session.execute(
        text("SELECT * FROM ai_recommendations WHERE borrower_id = :b ORDER BY generated_at DESC"),
        {"b": borrower_id}
    )
    rows = result.mappings().all()

    return [dict(r) for r in rows]


# ── GET /risk/graph/{borrower_id} ──────────────────────────────────────────────
@router.get("/graph/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def get_borrower_knowledge_graph(
    borrower_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Dynamically builds Knowledge Graph nodes and edges from PostgreSQL data with tenant isolation and deduplication."""
    # 1. Borrower node with strict tenant isolation and archive check
    res_b = await session.execute(
        text("""
            SELECT id, company_name, sector, country, risk_rating_level
            FROM borrowers
            WHERE id = :b AND organization_id = :org_id AND is_archived = FALSE
        """),
        {"b": borrower_id, "org_id": current_user.organization_id}
    )
    b = res_b.mappings().first()
    if not b:
        raise HTTPException(status_code=404, detail="Borrower not found.")

    res_h = await session.execute(
        text("SELECT score, category FROM borrower_health_scores WHERE borrower_id = :b ORDER BY calculated_at DESC LIMIT 1"),
        {"b": borrower_id}
    )
    h = res_h.mappings().first()
    health_str = f"Health: {h['score']}/100 ({h['category']})" if h else "Health: Pending Analysis"

    nodes = [
        {
            "id": b["id"],
            "label": b["company_name"],
            "type": "borrower",
            "details": f"Borrower: {b['company_name']} | Sector: {b['sector']} | Country: {b['country']} | Rating: {b['risk_rating_level']} | {health_str}",
            "x": 100,
            "y": 220
        }
    ]
    edges = []

    # 2. Loans for borrower (active only)
    res_loans = await session.execute(
        text("""
            SELECT id, agreement_id, principal_amount, currency, interest_rate, status
            FROM loans
            WHERE borrower_id = :b AND is_archived = FALSE
            ORDER BY start_date DESC
        """),
        {"b": borrower_id}
    )
    loans = res_loans.mappings().all()

    for idx, l in enumerate(loans):
        l_node_id = f"loan_{l['id']}"
        l_amount = float(l["principal_amount"]) if l["principal_amount"] else 0.0
        l_curr = l["currency"] or "USD"
        l_y = 130 + (idx * 140)

        nodes.append({
            "id": l_node_id,
            "label": f"Facility ({l_curr} ${l_amount/1e6:.1f}M)",
            "type": "loan",
            "details": f"Loan Facility | Principal: {l_curr} ${l_amount:,.2f} | Status: {l['status']}",
            "x": 280,
            "y": l_y
        })
        edges.append({"from": b["id"], "to": l_node_id})

        # 3. Active Agreement(s) for this loan (prioritize latest uploaded agreement)
        res_ag = await session.execute(
            text("""
                SELECT id, file_path, document_type, filing_type, processing_status, upload_date 
                FROM agreements 
                WHERE loan_id = :lid 
                ORDER BY upload_date DESC 
                LIMIT 1
            """),
            {"lid": l["id"]}
        )
        ag = res_ag.mappings().first()
        if not ag and l.get("agreement_id"):
            res_ag = await session.execute(
                text("SELECT id, file_path, document_type, filing_type, processing_status, upload_date FROM agreements WHERE id = :ag_id"),
                {"ag_id": l["agreement_id"]}
            )
            ag = res_ag.mappings().first()

        if ag:
            ag_node_id = f"ag_{ag['id']}"
            raw_path = ag["file_path"] or ""
            base_name = raw_path.split("/")[-1] if raw_path else "Credit Agreement"
            clean_name = re.sub(r"^[0-9a-fA-F-]{36}_", "", base_name)
            if clean_name.startswith("sec_filing_"):
                doc_type_clean = (ag.get("filing_type") or ag.get("document_type") or "SEC Filing").replace("_", " ").upper()
                clean_name = f"SEC {doc_type_clean}" if not doc_type_clean.startswith("SEC") else doc_type_clean
            if len(clean_name) > 22:
                clean_name = clean_name[:20] + "…"

            ag_y = l_y
            nodes.append({
                "id": ag_node_id,
                "label": clean_name,
                "type": "agreement",
                "details": f"Document: {clean_name} | Type: {ag['document_type'].upper()} | Status: {ag['processing_status']}",
                "x": 480,
                "y": ag_y
            })
            edges.append({"from": l_node_id, "to": ag_node_id})

            # 4. Deduplicated Covenants for this active agreement
            res_covs = await session.execute(
                text("""
                    SELECT DISTINCT ON (name)
                        id, name, covenant_type, threshold, threshold_direction, formula
                    FROM covenants
                    WHERE agreement_id = :ag_id
                    ORDER BY name, extracted_at DESC
                """),
                {"ag_id": ag["id"]}
            )
            covs = res_covs.mappings().all()

            for c_idx, cov in enumerate(covs):
                cov_node_id = f"cov_{cov['id']}"
                thresh_val = float(cov["threshold"]) if cov["threshold"] is not None else "N/A"
                dir_sym = "≤" if (cov["threshold_direction"] or "").lower() == "max" else ("≥" if (cov["threshold_direction"] or "").lower() == "min" else "")
                cov_label = cov["name"].replace(" Maintenance", "")
                if len(cov_label) > 22:
                    cov_label = cov_label[:20] + "…"

                cov_y = (ag_y - 40) + (c_idx * 80)
                nodes.append({
                    "id": cov_node_id,
                    "label": cov_label,
                    "type": "covenant",
                    "details": f"Covenant: {cov['name']} | Type: {cov['covenant_type']} | Threshold: {dir_sym} {thresh_val} | Formula: {cov['formula'] or 'N/A'}",
                    "x": 680,
                    "y": cov_y
                })
                edges.append({"from": ag_node_id, "to": cov_node_id})

    # 5. Financial Metrics (latest for this borrower or attached agreements)
    res_fin = await session.execute(
        text("""
            SELECT fm.* 
            FROM financial_metrics fm
            JOIN agreements a ON fm.agreement_id = a.id
            JOIN loans l ON a.loan_id = l.id
            WHERE l.borrower_id = :b
            ORDER BY fm.extracted_at DESC 
            LIMIT 1
        """),
        {"b": borrower_id}
    )
    fin = res_fin.mappings().first()
    if not fin:
        res_fin = await session.execute(
            text("SELECT * FROM financial_metrics WHERE borrower_id = :b ORDER BY extracted_at DESC LIMIT 1"),
            {"b": borrower_id}
        )
        fin = res_fin.mappings().first()
    if fin:
        fin_node_id = f"fin_{fin['id']}"
        lev_str = f"{fin['leverage_ratio']:.2f}x" if fin["leverage_ratio"] is not None else "N/A"
        cov_str = f"{fin['interest_coverage']:.2f}x" if fin["interest_coverage"] is not None else "N/A"
        rev_str = f"${float(fin['revenue']):,.2f}" if fin["revenue"] is not None else "N/A"
        ebitda_str = f"${float(fin['ebitda']):,.2f}" if fin["ebitda"] is not None else "N/A"
        debt_str = f"${float(fin['total_debt']):,.2f}" if fin["total_debt"] is not None else "N/A"
        nodes.append({
            "id": fin_node_id,
            "label": f"Financials ({fin['reporting_period'][:12] if fin['reporting_period'] else 'Latest'})",
            "type": "financial",
            "details": (
                f"Financial Metrics | "
                f"Revenue: {rev_str} | "
                f"EBITDA: {ebitda_str} | "
                f"Total Debt: {debt_str} | "
                f"Leverage: {lev_str} | "
                f"Coverage: {cov_str}"
            ),
            "x": 280,
            "y": 340
        })
        edges.append({"from": b["id"], "to": fin_node_id})

    return {"nodes": nodes, "edges": edges}


# ── POST /risk/pipeline/{borrower_id} ──────────────────────────────────────────
@router.post("/pipeline/{borrower_id}", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def trigger_risk_pipeline(
    borrower_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Manually triggers full Risk Intelligence Pipeline recalculation."""
    pipeline = RiskIntelligencePipeline()
    res = await pipeline.run_full_pipeline(session, borrower_id)
    return res
