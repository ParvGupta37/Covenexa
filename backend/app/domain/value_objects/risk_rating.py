"""
Risk Rating Value Object.
Defines risk classification for borrowers.
"""
from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class RiskRating:
    level: RiskLevel
    score: int  # Numerical risk rating metric, e.g., 1 (best) to 10 (worst)

    def __post_init__(self) -> None:
        if not (1 <= self.score <= 10):
            raise ValueError("Risk score must be an integer between 1 and 10.")
        
        # Simple cross-validation
        if self.level == RiskLevel.LOW and self.score > 3:
            raise ValueError("LOW risk level cannot have a score greater than 3.")
        if self.level == RiskLevel.CRITICAL and self.score < 8:
            raise ValueError("CRITICAL risk level cannot have a score less than 8.")

    def __str__(self) -> str:
        return f"{self.level} (Score: {self.score})"
