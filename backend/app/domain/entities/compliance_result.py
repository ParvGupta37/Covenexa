"""
Compliance Result domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ComplianceStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    BREACHED = "BREACHED"
    WARNING = "WARNING"


@dataclass
class ComplianceResult:
    id: str
    borrower_id: str
    covenant_id: str
    status: ComplianceStatus
    headroom: float  # e.g., 0.15 for 15% headroom remaining
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
