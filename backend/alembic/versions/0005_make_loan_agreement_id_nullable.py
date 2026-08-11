"""make loan agreement_id nullable

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-10 14:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('loans', 'agreement_id', existing_type=sa.String(length=36), nullable=True)


def downgrade() -> None:
    op.alter_column('loans', 'agreement_id', existing_type=sa.String(length=36), nullable=False)
