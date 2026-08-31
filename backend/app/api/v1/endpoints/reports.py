"""
Reports API Endpoints — Sprint 4.
Provides endpoints for Executive Credit Memorandum and Report Generation.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role, get_current_user
from app.domain.entities.user import User, UserRole
from ai.agents.reporting_agent import ReportingAgent
from app.api.v1.endpoints.audit import log_audit_event

router = APIRouter(prefix="/reports", tags=["Reports"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.get(
    "/credit-memo/{borrower_id}",
    response_model=Dict[str, Any],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def generate_credit_memo(
    borrower_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Dict[str, Any]:
    """Generate an Executive Credit Memorandum report for a borrower."""

    # 1. Fetch Borrower
    res_b = await session.execute(
        text("SELECT id, company_name, sector, country, updated_at FROM borrowers WHERE id = :id"),
        {"id": borrower_id},
    )
    b_row = res_b.mappings().first()
    if not b_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Borrower entity not found.")

    borrower_dict = dict(b_row)

    # 2. Fetch Health & Risk Assessment
    res_h = await session.execute(
        text("SELECT score, category, explanation FROM borrower_health_scores WHERE borrower_id = :id ORDER BY calculated_at DESC LIMIT 1"),
        {"id": borrower_id},
    )
    h_row = res_h.mappings().first()
    health_dict = dict(h_row) if h_row else {"score": None, "category": "UNANALYZED"}

    res_d = await session.execute(
        text("SELECT default_probability, risk_category, z_score, risk_factors FROM risk_assessments WHERE borrower_id = :id ORDER BY assessed_at DESC LIMIT 1"),
        {"id": borrower_id},
    )
    d_row = res_d.mappings().first()
    default_dict = dict(d_row) if d_row else {"default_probability": None, "risk_category": "UNANALYZED", "z_score": None, "risk_factors": ["No risk assessment performed yet for this entity."]}
    if isinstance(default_dict.get("risk_factors"), str):
        import json
        try:
            default_dict["risk_factors"] = json.loads(default_dict["risk_factors"])
        except:
            default_dict["risk_factors"] = []

    # 3. Fetch Financial Metrics
    res_f = await session.execute(
        text("SELECT revenue, ebitda, net_income, total_debt, cash, leverage_ratio, interest_coverage, currency FROM financial_metrics WHERE borrower_id = :id ORDER BY extracted_at DESC LIMIT 1"),
        {"id": borrower_id},
    )
    f_row = res_f.mappings().first()
    fin_dict = {k: (float(v) if v is not None and k != "currency" else v) for k, v in dict(f_row).items()} if f_row else {}

    # 4. Fetch Covenant Monitoring
    res_c = await session.execute(
        text("""
            SELECT cm.id, c.name as covenant_name, c.covenant_type, cm.status, cm.current_value, cm.threshold_value, cm.headroom_pct, cm.reason
            FROM covenant_monitoring cm
            JOIN covenants c ON c.id = cm.covenant_id
            WHERE cm.borrower_id = :id
            ORDER BY cm.checked_at DESC
        """),
        {"id": borrower_id},
    )
    c_rows = res_c.mappings().all()
    covenants_list = [{k: (float(v) if isinstance(v, (int, float)) else v) for k, v in dict(r).items()} for r in c_rows]

    # 5. Fetch Facilities / Loans
    res_l = await session.execute(
        text("SELECT id, loan_type, interest_rate, maturity_date FROM loans WHERE borrower_id = :id"),
        {"id": borrower_id},
    )
    l_rows = res_l.mappings().all()
    loans_list = [dict(r) for r in l_rows]

    # 6. Fetch Latest Stress Simulation if available
    res_s = await session.execute(
        text("SELECT scenario_name, projected_health_score, projected_default_prob, covenant_breaches_count, at_risk FROM stress_test_simulations WHERE borrower_id = :id ORDER BY created_at DESC LIMIT 1"),
        {"id": borrower_id},
    )
    s_row = res_s.mappings().first()
    stress_dict = dict(s_row) if s_row else None

    # 7. Run Reporting Agent
    agent = ReportingAgent()
    memo = agent.generate_credit_memo(
        borrower=borrower_dict,
        health=health_dict,
        default_pred=default_dict,
        covenants=covenants_list,
        financials=fin_dict,
        loans=loans_list,
        stress=stress_dict,
    )

    # 8. Log Audit event
    await log_audit_event(
        action="credit_memo_generated",
        resource_type="report",
        resource_id=borrower_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"company_name": borrower_dict.get("company_name")},
    )

    return memo
