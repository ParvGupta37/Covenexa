"""
User API schemas.
"""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    role: str
    organization_id: Optional[str] = None
    created_at: datetime

    @field_validator("email", mode="before")
    @classmethod
    def parse_email_vo(cls, v: Any) -> str:
        """Handle Email Value Object serialization."""
        if hasattr(v, "value"):
            return v.value
        return str(v)
