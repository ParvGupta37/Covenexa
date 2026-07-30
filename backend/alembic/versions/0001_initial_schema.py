"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-07-05 19:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ORGANIZATIONS ─────────────────────────────────────────────
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organizations_name'), 'organizations', ['name'], unique=True)

    # ── USERS ─────────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # ── BORROWERS ─────────────────────────────────────────────────
    op.create_table(
        'borrowers',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('company_name', sa.String(length=100), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('risk_rating_level', sa.String(length=20), nullable=False),
        sa.Column('risk_rating_score', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── LOANS ─────────────────────────────────────────────────────
    op.create_table(
        'loans',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('borrower_id', sa.String(length=36), nullable=False),
        sa.Column('agreement_id', sa.String(length=36), nullable=False),
        sa.Column('principal_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('interest_rate', sa.Float(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('maturity_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── AGREEMENTS ────────────────────────────────────────────────
    op.create_table(
        'agreements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('loan_id', sa.String(length=36), nullable=False),
        sa.Column('version', sa.String(length=20), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('upload_date', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['loan_id'], ['loans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── FINANCIAL STATEMENTS ──────────────────────────────────────
    op.create_table(
        'financial_statements',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('borrower_id', sa.String(length=36), nullable=False),
        sa.Column('reporting_period', sa.String(length=50), nullable=False),
        sa.Column('revenue', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('ebitda', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('total_debt', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('cash', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── COMPLIANCE RESULTS ────────────────────────────────────────
    op.create_table(
        'compliance_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('borrower_id', sa.String(length=36), nullable=False),
        sa.Column('covenant_id', sa.String(length=36), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('headroom', sa.Float(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── REPORTS ───────────────────────────────────────────────────
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('borrower_id', sa.String(length=36), nullable=False),
        sa.Column('report_type', sa.String(length=50), nullable=False),
        sa.Column('report_path', sa.String(length=500), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('compliance_results')
    op.drop_table('financial_statements')
    op.drop_table('agreements')
    op.drop_table('loans')
    op.drop_table('borrowers')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_organizations_name'), table_name='organizations')
    op.drop_table('organizations')
#
