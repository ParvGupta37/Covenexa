"""add archival columns to borrowers and loans

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-30 12:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0008'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add archival columns to borrowers
    op.add_column(
        'borrowers',
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'))
    )
    op.add_column(
        'borrowers',
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'borrowers',
        sa.Column('archived_by', sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        'fk_borrowers_archived_by',
        'borrowers',
        'users',
        ['archived_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_borrowers_is_archived', 'borrowers', ['is_archived'])

    # 2. Add archival columns to loans
    op.add_column(
        'loans',
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('FALSE'))
    )
    op.add_column(
        'loans',
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'loans',
        sa.Column('archived_by', sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        'fk_loans_archived_by',
        'loans',
        'users',
        ['archived_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_loans_is_archived', 'loans', ['is_archived'])


def downgrade() -> None:
    # Drop from loans
    op.drop_constraint('fk_loans_archived_by', 'loans', type_='foreignkey')
    op.drop_index('ix_loans_is_archived', table_name='loans')
    op.drop_column('loans', 'archived_by')
    op.drop_column('loans', 'archived_at')
    op.drop_column('loans', 'is_archived')

    # Drop from borrowers
    op.drop_constraint('fk_borrowers_archived_by', 'borrowers', type_='foreignkey')
    op.drop_index('ix_borrowers_is_archived', table_name='borrowers')
    op.drop_column('borrowers', 'archived_by')
    op.drop_column('borrowers', 'archived_at')
    op.drop_column('borrowers', 'is_archived')
