"""
Organization domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Organization:
    id: str
    name: str
    industry: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
