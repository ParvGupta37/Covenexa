"""
SQLAlchemy ORM model for Borrowers.
"""
import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.entities.borrower import Borrower
from app.domain.value_objects.risk_rating import RiskLevel, RiskRating
from app.infrastructure.orm.base import Base


class BorrowerORM(Base):
    __tablename__ = "borrowers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    company_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sector: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Store RiskRating value object fields in individual database columns
    risk_rating_level: Mapped[str] = mapped_column(String(20), nullable=False, default=RiskLevel.MEDIUM.value)
    risk_rating_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    def to_entity(self) -> Borrower:
        return Borrower(
            id=self.id,
            organization_id=self.organization_id,
            company_name=self.company_name,
            sector=self.sector,
            country=self.country,
            risk_rating=RiskRating(
                level=RiskLevel(self.risk_rating_level),
                score=self.risk_rating_score,
            ),
        )

    @classmethod
    def from_entity(cls, entity: Borrower) -> "BorrowerORM":
        return cls(
            id=entity.id,
            organization_id=entity.organization_id,
            company_name=entity.company_name,
            sector=entity.sector,
            country=entity.country,
            risk_rating_level=entity.risk_rating.level.value,
            risk_rating_score=entity.risk_rating.score,
        )
