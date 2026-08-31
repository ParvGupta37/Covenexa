"""
SQLAlchemy ORM models for Copilot Conversations and Messages.
Provides persistent chat history, evidence persistence, and multi-tenant isolation.
"""
from datetime import datetime, timezone
import uuid
from typing import Any, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.orm.base import Base


class CopilotConversationORM(Base):
    """
    Represents an ongoing or archived Copilot conversational thread.
    Scoped to an organization (tenant) and optionally linked to a specific borrower.
    """
    __tablename__ = "copilot_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    borrower_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("borrowers.id", ondelete="CASCADE"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    messages: Mapped[List["CopilotMessageORM"]] = relationship(
        "CopilotMessageORM",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="CopilotMessageORM.message_index",
    )


class CopilotMessageORM(Base):
    """
    Represents an individual message in a Copilot conversation.
    Stores query, synthesized response, and full structured citations & hybrid retrieval evidence.
    """
    __tablename__ = "copilot_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("copilot_conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Structured evidence & citations persistence
    citations: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    hybrid_retrieval_status: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    evidence_sources: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    
    message_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), index=True
    )

    conversation: Mapped["CopilotConversationORM"] = relationship(
        "CopilotConversationORM",
        back_populates="messages",
    )
