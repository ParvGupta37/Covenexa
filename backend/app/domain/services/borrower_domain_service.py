"""
Borrower Domain Service.
Contains purely logical borrower analysis rules (e.g. status changes based on risk scores)
without database I/O.
"""
from app.domain.entities.borrower import Borrower
from app.domain.value_objects.risk_rating import RiskLevel


class BorrowerDomainService:
    """
    Pure domain rules regarding borrower health classifications.
    """

    @staticmethod
    def requires_immediate_review(borrower: Borrower) -> bool:
        """
        Determines if a borrower requires immediate portfolio review.
        Rule: RiskRating level is CRITICAL or score is >= 9.
        """
        return (
            borrower.risk_rating.level == RiskLevel.CRITICAL
            or borrower.risk_rating.score >= 9
        )
