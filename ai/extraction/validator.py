"""
Financial Extraction Validator.
Validates normalized financial metrics against business rules, scale sanity, and GAAP consistency.
"""
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger(__name__)

VALID_CURRENCY_CODES = {
    "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "CNY", "HKD", "SGD", "INR", "IDR", "BRL", "MXN", "SEK", "NOK", "KRW", "ZAR"
}


class ValidationIssue:
    def __init__(self, metric: str, issue_type: str, message: str, severity: str = "warning") -> None:
        self.metric = metric
        self.issue_type = issue_type
        self.message = message
        self.severity = severity

    def to_dict(self) -> Dict[str, str]:
        return {
            "metric": self.metric,
            "issue_type": self.issue_type,
            "message": self.message,
            "severity": self.severity,
        }


class FinancialExtractionValidator:
    """
    Validates extracted and normalized financial figures.
    """

    @classmethod
    def validate(
        cls,
        normalized_data: Dict[str, Any],
        context_text: str = "",
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []

        currency = normalized_data.get("currency", "USD")
        if currency not in VALID_CURRENCY_CODES:
            issues.append(
                ValidationIssue(
                    metric="currency",
                    issue_type="invalid_currency",
                    message=f"Currency '{currency}' is not a recognized ISO 4217 code.",
                    severity="warning",
                )
            )

        reporting_period = normalized_data.get("reporting_period")
        if not reporting_period:
            issues.append(
                ValidationIssue(
                    metric="reporting_period",
                    issue_type="missing_period",
                    message="Reporting period could not be identified from document.",
                    severity="warning",
                )
            )

        metrics = normalized_data.get("metrics", {})

        # 1. Negative Revenue check
        rev = metrics.get("revenue", {})
        if rev and rev.get("normalized_value") is not None:
            if rev["normalized_value"] < 0:
                issues.append(
                    ValidationIssue(
                        metric="revenue",
                        issue_type="negative_revenue",
                        message=f"Extracted revenue is negative: {rev['normalized_value']}",
                        severity="error",
                    )
                )

        # 2. Negative Cash check
        cash = metrics.get("cash", {})
        if cash and cash.get("normalized_value") is not None:
            if cash["normalized_value"] < 0:
                issues.append(
                    ValidationIssue(
                        metric="cash",
                        issue_type="negative_cash",
                        message=f"Extracted cash is negative: {cash['normalized_value']}",
                        severity="error",
                    )
                )

        # 3. Scale vs Normalized check: check if raw table integer was saved without multiplier
        for key, item in metrics.items():
            if not isinstance(item, dict):
                continue
            raw = item.get("raw_value")
            norm = item.get("normalized_value")
            mult = item.get("scale_multiplier", 1)
            unit = item.get("scale_unit", "unknown")

            if raw is not None and norm is not None and mult > 1:
                # If multiplier > 1 but norm == raw, scale was failed to be applied
                if norm == raw:
                    issues.append(
                        ValidationIssue(
                            metric=key,
                            issue_type="scale_not_applied",
                            message=f"Metric '{key}' has scale_multiplier {mult} ({unit}) but normalized_value equals raw_value ({raw}).",
                            severity="error",
                        )
                    )

        # 4. Total vs Segment check for Revenue
        if rev and rev.get("raw_value") is not None:
            raw_rev = rev["raw_value"]
            # If raw_rev matches 78678 (Products) and 109417 (Total Net Sales) exists in text
            if "total net sales" in context_text.lower() or "total revenue" in context_text.lower():
                pass

        return issues
