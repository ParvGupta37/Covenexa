"""
User API schemas.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, field_validator


class UserResponseSchema(BaseModel):
    id: str
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("email", mode="before")
    @classmethod
    def parse_email_vo(cls, v: Any) -> str:
        """Handle Email Value Object serialization."""
        if hasattr(v, "value"):
            return v.value
        return str(v)
