"""Sprint 2 — Document Processing Pipeline Schema

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10

New tables:
  - document_chunks    (semantic text chunks per agreement)
  - covenants          (AI-extracted covenant clauses)
  - financial_metrics  (AI-extracted financial metrics)

Modified tables:
  - agreements         (add processing pipeline status columns)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ALTER agreements — add Sprint 2 processing columns ────────────────
    op.add_column('agreements', sa.Column('document_type', sa.String(50), nullable=False, server_default='loan_agreement'))
    op.add_column('agreements', sa.Column('processing_status', sa.String(30), nullable=False, server_default='pending'))
    op.add_column('agreements', sa.Column('processing_error', sa.Text(), nullable=True))
    op.add_column('agreements', sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('agreements', sa.Column('page_count', sa.Integer(), nullable=True))
    op.add_column('agreements', sa.Column('chunk_count', sa.Integer(), nullable=True))

    # ── document_chunks ───────────────────────────────────────────────────
    op.create_table(
        'document_chunks',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('agreement_id', sa.String(36), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('section', sa.String(500), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('char_count', sa.Integer(), nullable=False),
        sa.Column('embedding_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_chunks_agreement_id', 'document_chunks', ['agreement_id'])

    # ── covenants ─────────────────────────────────────────────────────────
    op.create_table(
        'covenants',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('agreement_id', sa.String(36), nullable=False),
        sa.Column('borrower_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('covenant_type', sa.String(50), nullable=False),
        sa.Column('formula', sa.Text(), nullable=True),
        sa.Column('threshold', sa.Float(), nullable=True),
        sa.Column('threshold_direction', sa.String(10), nullable=True),
        sa.Column('frequency', sa.String(50), nullable=True),
        sa.Column('cure_period_days', sa.Integer(), nullable=True),
        sa.Column('is_event_of_default', sa.Boolean(), nullable=False),
        sa.Column('amendment_references', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['agreements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_covenants_agreement_id', 'covenants', ['agreement_id'])
    op.create_index('ix_covenants_borrower_id', 'covenants', ['borrower_id'])

    # ── financial_metrics ────────────────────────────────────────────────
    op.create_table(
        'financial_metrics',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('agreement_id', sa.String(36), nullable=False),
        sa.Column('borrower_id', sa.String(36), nullable=False),
        sa.Column('reporting_period', sa.String(50), nullable=True),
        sa.Column('revenue', sa.Numeric(20, 2), nullable=True),
        sa.Column('ebitda', sa.Numeric(20, 2), nullable=True),
        sa.Column('net_income', sa.Numeric(20, 2), nullable=True),
        sa.Column('total_debt', sa.Numeric(20, 2), nullable=True),
        sa.Column('cash', sa.Numeric(20, 2), nullable=True),
        sa.Column('interest_expense', sa.Numeric(20, 2), nullable=True),
        sa.Column('leverage_ratio', sa.Float(), nullable=True),
        sa.Column('interest_coverage', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('extracted_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['agreements.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_financial_metrics_agreement_id', 'financial_metrics', ['agreement_id'])
    op.create_index('ix_financial_metrics_borrower_id', 'financial_metrics', ['borrower_id'])


def downgrade() -> None:
    op.drop_table('financial_metrics')
    op.drop_index('ix_covenants_borrower_id', table_name='covenants')
    op.drop_index('ix_covenants_agreement_id', table_name='covenants')
    op.drop_table('covenants')
    op.drop_index('ix_document_chunks_agreement_id', table_name='document_chunks')
    op.drop_table('document_chunks')
    op.drop_column('agreements', 'chunk_count')
    op.drop_column('agreements', 'page_count')
    op.drop_column('agreements', 'processed_at')
    op.drop_column('agreements', 'processing_error')
    op.drop_column('agreements', 'processing_status')
    op.drop_column('agreements', 'document_type')
