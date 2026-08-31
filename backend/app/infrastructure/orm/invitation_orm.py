"""
SQLAlchemy ORM model for Organization Invitations.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.invitation import Invitation
from app.domain.entities.user import UserRole
from app.infrastructure.orm.base import Base


class InvitationORM(Base):
    __tablename__ = "invitations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.ANALYST.value)
    token: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_entity(self) -> Invitation:
        return Invitation(
            id=self.id,
            organization_id=self.organization_id,
            email=self.email,
            token=self.token,
            role=UserRole(self.role),
            name=self.name,
            status=self.status,
            created_at=self.created_at,
            expires_at=self.expires_at,
        )

    @classmethod
    def from_entity(cls, entity: Invitation) -> "InvitationORM":
        return cls(
            id=entity.id,
            organization_id=entity.organization_id,
            email=entity.email,
            name=entity.name,
            role=entity.role.value if hasattr(entity.role, "value") else str(entity.role),
            token=entity.token,
            status=entity.status,
            created_at=entity.created_at,
            expires_at=entity.expires_at,
        )
