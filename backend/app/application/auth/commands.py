"""
Authentication application commands.
"""
from dataclasses import dataclass
from app.domain.entities.user import UserRole


@dataclass
class RegisterCommand:
    name: str
    email: str
    password: str
    role: str = "ANALYST"


@dataclass
class LoginCommand:
    email: str
    password: str
