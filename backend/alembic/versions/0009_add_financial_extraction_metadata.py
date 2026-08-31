"""add extraction_metadata to financial_metrics

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-30 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0009'
down_revision: Union[str, None] = '0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'financial_metrics',
        sa.Column('extraction_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('financial_metrics', 'extraction_metadata')
