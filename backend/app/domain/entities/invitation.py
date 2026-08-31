"""
Invitation domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from app.domain.entities.user import UserRole


@dataclass
class Invitation:
    id: str
    organization_id: str
    email: str
    token: str
    role: UserRole = UserRole.ANALYST
    name: Optional[str] = None
    status: str = "PENDING"  # PENDING, ACCEPTED, REVOKED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
