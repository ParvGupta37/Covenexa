"""add loan agreement_id foreign key

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-10 14:50:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '0006'
down_revision: Union[str, None] = '0005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Clean up non-existent foreign key string references
    op.execute(
        "UPDATE loans SET agreement_id = NULL WHERE agreement_id IS NOT NULL AND agreement_id NOT IN (SELECT id FROM agreements)"
    )
    # 2. Add foreign key constraint to agreements.id with ON DELETE SET NULL
    op.create_foreign_key(
        "fk_loans_agreement_id",
        "loans",
        "agreements",
        ["agreement_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_loans_agreement_id", "loans", type_="foreignkey")
