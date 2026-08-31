"""add organization_id to users and create invitations table

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-30 11:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add organization_id column to users table
    op.add_column(
        'users',
        sa.Column('organization_id', sa.String(length=36), nullable=True)
    )
    op.create_foreign_key(
        'fk_users_organization_id',
        'users',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_users_organization_id', 'users', ['organization_id'])

    # Associate any existing users with the first organization if one exists
    op.execute("""
        UPDATE users
        SET organization_id = (SELECT id FROM organizations ORDER BY created_at ASC LIMIT 1)
        WHERE organization_id IS NULL AND EXISTS (SELECT 1 FROM organizations);
    """)

    # 2. Create invitations table
    op.create_table(
        'invitations',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('organization_id', sa.String(length=36), sa.ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='ANALYST'),
        sa.Column('token', sa.String(length=100), nullable=False, unique=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_invitations_token', 'invitations', ['token'], unique=True)
    op.create_index('ix_invitations_email', 'invitations', ['email'])
    op.create_index('ix_invitations_organization_id', 'invitations', ['organization_id'])


def downgrade() -> None:
    op.drop_table('invitations')
    op.drop_constraint('fk_users_organization_id', 'users', type_='foreignkey')
    op.drop_index('ix_users_organization_id', table_name='users')
    op.drop_column('users', 'organization_id')
