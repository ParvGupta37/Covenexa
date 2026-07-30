"""
Report domain entity.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class ReportType(str, Enum):
    PORTFOLIO_SUMMARY = "PORTFOLIO_SUMMARY"
    BORROWER_HEALTH = "BORROWER_HEALTH"
    COVENANT_AUDIT = "COVENANT_AUDIT"


@dataclass
class Report:
    id: str
    borrower_id: str
    report_type: ReportType
    report_path: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
