"""
Sprint 3 — AI Risk Intelligence Engine tables.

Adds:
- borrower_health_scores    (health score history per borrower)
- risk_assessments          (default prediction per borrower)
- covenant_monitoring       (per-covenant compliance results with reasoning)
- alerts                    (severity-based system alerts)
- stress_test_results       (scenario simulation results)
- ai_recommendations        (AI-generated action items)
- Extends agreements        (source_url, source_type, filing_type, sec_cik)
- Extends financial_metrics (net_debt, current_ratio, quick_ratio, dscr, free_cash_flow, debt_to_equity)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend agreements ─────────────────────────────────────────────────────
    op.add_column("agreements", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("agreements", sa.Column("source_type", sa.String(20), nullable=False, server_default="upload"))
    op.add_column("agreements", sa.Column("filing_type", sa.String(20), nullable=True))
    op.add_column("agreements", sa.Column("sec_cik", sa.String(20), nullable=True))

    # ── Extend financial_metrics ───────────────────────────────────────────────
    op.add_column("financial_metrics", sa.Column("net_debt", sa.Numeric(20, 2), nullable=True))
    op.add_column("financial_metrics", sa.Column("current_ratio", sa.Float(), nullable=True))
    op.add_column("financial_metrics", sa.Column("quick_ratio", sa.Float(), nullable=True))
    op.add_column("financial_metrics", sa.Column("debt_to_equity", sa.Float(), nullable=True))
    op.add_column("financial_metrics", sa.Column("dscr", sa.Float(), nullable=True))
    op.add_column("financial_metrics", sa.Column("free_cash_flow", sa.Numeric(20, 2), nullable=True))

    # ── borrower_health_scores ────────────────────────────────────────────────
    op.create_table(
        "borrower_health_scores",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),  # excellent | good | moderate | high_risk | critical
        sa.Column("financial_score", sa.Float(), nullable=True),
        sa.Column("compliance_score", sa.Float(), nullable=True),
        sa.Column("liquidity_score", sa.Float(), nullable=True),
        sa.Column("leverage_score", sa.Float(), nullable=True),
        sa.Column("trend_score", sa.Float(), nullable=True),
        sa.Column("explanation", sa.Text(), nullable=True),   # JSON string of factor breakdown
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── risk_assessments ──────────────────────────────────────────────────────
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("default_probability", sa.Float(), nullable=False),
        sa.Column("risk_category", sa.String(20), nullable=False),  # low | medium | high | critical
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("z_score", sa.Float(), nullable=True),
        sa.Column("risk_factors", sa.Text(), nullable=True),  # JSON list of top factors
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── covenant_monitoring ───────────────────────────────────────────────────
    op.create_table(
        "covenant_monitoring",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("covenant_id", sa.String(36), sa.ForeignKey("covenants.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False),  # healthy | warning | breach | critical
        sa.Column("current_value", sa.Float(), nullable=True),
        sa.Column("threshold_value", sa.Float(), nullable=True),
        sa.Column("headroom_pct", sa.Float(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── alerts ────────────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("alert_type", sa.String(50), nullable=False),  # covenant_breach | health_drop | default_risk | financial_deterioration
        sa.Column("severity", sa.String(20), nullable=False),    # info | warning | high | critical
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("metadata", sa.Text(), nullable=True),  # JSON
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── stress_test_results ───────────────────────────────────────────────────
    op.create_table(
        "stress_test_results",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("scenario_name", sa.String(100), nullable=False),
        sa.Column("revenue_change_pct", sa.Float(), nullable=True),
        sa.Column("ebitda_change_pct", sa.Float(), nullable=True),
        sa.Column("interest_rate_change_bps", sa.Float(), nullable=True),
        sa.Column("debt_change_pct", sa.Float(), nullable=True),
        sa.Column("projected_health_score", sa.Float(), nullable=True),
        sa.Column("projected_default_prob", sa.Float(), nullable=True),
        sa.Column("covenant_breaches_count", sa.Integer(), nullable=True),
        sa.Column("at_risk", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("results_json", sa.Text(), nullable=True),  # full JSON result
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── ai_recommendations ────────────────────────────────────────────────────
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("borrower_id", sa.String(36), sa.ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("recommendation_type", sa.String(50), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False),  # low | medium | high | urgent
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column("action_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_actioned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_recommendations")
    op.drop_table("stress_test_results")
    op.drop_table("alerts")
    op.drop_table("covenant_monitoring")
    op.drop_table("risk_assessments")
    op.drop_table("borrower_health_scores")

    for col in ["net_debt", "current_ratio", "quick_ratio", "debt_to_equity", "dscr", "free_cash_flow"]:
        op.drop_column("financial_metrics", col)

    for col in ["source_url", "source_type", "filing_type", "sec_cik"]:
        op.drop_column("agreements", col)
