"""add copilot conversations and messages

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-30 22:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '0010'
down_revision: Union[str, None] = '0009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'copilot_conversations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('borrower_id', sa.String(length=36), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False, server_default='New Conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['borrower_id'], ['borrowers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_conversations_organization_id'), 'copilot_conversations', ['organization_id'], unique=False)
    op.create_index(op.f('ix_copilot_conversations_user_id'), 'copilot_conversations', ['user_id'], unique=False)
    op.create_index(op.f('ix_copilot_conversations_borrower_id'), 'copilot_conversations', ['borrower_id'], unique=False)
    op.create_index(op.f('ix_copilot_conversations_updated_at'), 'copilot_conversations', ['updated_at'], unique=False)

    op.create_table(
        'copilot_messages',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('conversation_id', sa.String(length=36), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('citations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('hybrid_retrieval_status', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('evidence_sources', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('message_index', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['conversation_id'], ['copilot_conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_copilot_messages_conversation_id'), 'copilot_messages', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_copilot_messages_created_at'), 'copilot_messages', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_copilot_messages_created_at'), table_name='copilot_messages')
    op.drop_index(op.f('ix_copilot_messages_conversation_id'), table_name='copilot_messages')
    op.drop_table('copilot_messages')

    op.drop_index(op.f('ix_copilot_conversations_updated_at'), table_name='copilot_conversations')
    op.drop_index(op.f('ix_copilot_conversations_borrower_id'), table_name='copilot_conversations')
    op.drop_index(op.f('ix_copilot_conversations_user_id'), table_name='copilot_conversations')
    op.drop_index(op.f('ix_copilot_conversations_organization_id'), table_name='copilot_conversations')
    op.drop_table('copilot_conversations')
