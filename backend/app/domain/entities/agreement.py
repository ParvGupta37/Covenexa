"""
Agreement domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Agreement:
    id: str
    loan_id: str
    version: str
    file_path: str
    upload_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
