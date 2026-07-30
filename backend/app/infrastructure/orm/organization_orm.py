"""
SQLAlchemy ORM model for Organizations.
"""
from datetime import datetime, timezone
import uuid

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.organization import Organization
from app.infrastructure.orm.base import Base


class OrganizationORM(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def to_entity(self) -> Organization:
        return Organization(
            id=self.id,
            name=self.name,
            industry=self.industry,
            created_at=self.created_at,
        )

    @classmethod
    def from_entity(cls, entity: Organization) -> "OrganizationORM":
        return cls(
            id=entity.id,
            name=entity.name,
            industry=entity.industry,
            created_at=entity.created_at,
        )
