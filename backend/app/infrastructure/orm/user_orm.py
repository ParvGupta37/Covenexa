"""
SQLAlchemy ORM model for Users.
"""
from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.user import User, UserRole
from app.domain.value_objects.email import Email
from app.infrastructure.orm.base import Base


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.ANALYST.value)
    organization_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_entity(self) -> User:
        return User(
            id=self.id,
            name=self.name,
            email=Email(self.email),
            password_hash=self.password_hash,
            role=UserRole(self.role),
            organization_id=self.organization_id,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: User) -> "UserORM":
        return cls(
            id=entity.id,
            name=entity.name,
            email=str(entity.email),
            password_hash=entity.password_hash,
            role=entity.role.value,
            organization_id=entity.organization_id,
            created_at=entity.created_at,
        )
