"""
User domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from app.domain.value_objects.email import Email


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    ANALYST = "ANALYST"


@dataclass
class User:
    id: str
    name: str
    email: Email
    password_hash: str
    role: UserRole
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update_role(self, new_role: UserRole) -> None:
        self.role = new_role
