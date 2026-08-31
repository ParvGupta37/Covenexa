"""
Scale Detector for Financial Statements and SEC Filings.
Deterministically detects table-level scale headers and inline monetary unit expressions
with document position-awareness and financial statement proximity ranking.
Also detects source document currency (ISO 4217).
"""
import re
from typing import Dict, List, Optional, Tuple, NamedTuple


class ScaleDetectionResult(NamedTuple):
    scale_unit: str          # "billions", "millions", "thousands", "units", "unknown"
    scale_multiplier: int    # 1_000_000_000, 1_000_000, 1_000, 1
    confidence: float        # 0.0 - 1.0
    matched_pattern: Optional[str] = None
    source_snippet: Optional[str] = None
    position: int = 0


# Canonical multipliers
SCALE_MULTIPLIERS: Dict[str, int] = {
    "trillions": 1_000_000_000_000,
    "trillion": 1_000_000_000_000,
    "t": 1_000_000_000_000,
    "billions": 1_000_000_000,
    "billion": 1_000_000_000,
    "b": 1_000_000_000,
    "millions": 1_000_000,
    "million": 1_000_000,
    "m": 1_000_000,
    "thousands": 1_000,
    "thousand": 1_000,
    "k": 1_000,
    "units": 1,
    "ones": 1,
    "dollars": 1,
    "exact": 1,
}

# Regex patterns for Scale Declarations in SEC Filings (10-K, 10-Q, 20-F, 6-K, 8-K)
SCALE_PATTERNS = [
    # Explicit parenthetical headers (e.g. '(In thousands, except per share data)', '(in billions of Rupiah)')
    (
        r"\(\s*(?:in|amounts in|\$ in|usd in|dollars in|expressed in)\s+(thousands?|millions?|billions?|trillions?)(?:[,\s]+[^\)]*)?\)",
        1.0,
    ),
    # Plain text scale declarations (e.g. 'dollars in millions', 'expressed in billions of Rupiah')
    (
        r"(?:in|amounts in|\$ in|usd in|dollars in|expressed in)\s+(thousands?|millions?|billions?|trillions?)\b",
        0.9,
    ),
]

# Currency detection patterns
CURRENCY_PATTERNS = [
    (r"(?:\b(?:rupiah|indonesian rupiah|idr)\b|rp\.?)", "IDR"),
    (r"(?:\b(?:euro|euros|eur)\b|€)", "EUR"),
    (r"(?:\b(?:pound|pounds|sterling|gbp)\b|£)", "GBP"),
    (r"(?:\b(?:yen|jpy)\b|¥)", "JPY"),
    (r"(?:\b(?:rupee|rupees|inr|lakhs?|crores?)\b|₹)", "INR"),
    (r"(?:\b(?:cad|canadian dollars?)\b|c\$)", "CAD"),
    (r"(?:\b(?:aud|australian dollars?)\b|a\$)", "AUD"),
    (r"\b(?:chf|swiss francs?)\b", "CHF"),
    (r"(?:\b(?:sgd|singapore dollars?)\b|s\$)", "SGD"),
    (r"(?:\b(?:usd|u\.s\.\s*dollars?|dollars?)\b|\$)", "USD"),
]


class ScaleDetector:
    """
    Detects financial statement scale indicators and native currency with position-awareness.
    """

    @classmethod
    def detect_table_scale(cls, text: str, anchor_pos: Optional[int] = None) -> ScaleDetectionResult:
        """
        Scans text for scale declarations.
        When anchor_pos is specified, prefers the scale declaration closest to (or immediately preceding)
        the anchor_pos. Otherwise, selects the first primary scale declaration found.
        """
        if not text:
            return ScaleDetectionResult(
                scale_unit="unknown",
                scale_multiplier=1,
                confidence=0.0,
            )

        matches: List[ScaleDetectionResult] = []

        for pattern, conf in SCALE_PATTERNS:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                snippet = m.group(0)
                raw_unit = m.group(1).lower()
                
                if "trillion" in raw_unit:
                    unit = "trillions"
                    multiplier = 1_000_000_000_000
                elif "billion" in raw_unit:
                    unit = "billions"
                    multiplier = 1_000_000_000
                elif "million" in raw_unit:
                    unit = "millions"
                    multiplier = 1_000_000
                elif "thousand" in raw_unit:
                    unit = "thousands"
                    multiplier = 1_000
                else:
                    unit = "units"
                    multiplier = 1

                matches.append(
                    ScaleDetectionResult(
                        scale_unit=unit,
                        scale_multiplier=multiplier,
                        confidence=conf,
                        matched_pattern=pattern,
                        source_snippet=snippet,
                        position=m.start(),
                    )
                )

        if not matches:
            return ScaleDetectionResult(
                scale_unit="unknown",
                scale_multiplier=1,
                confidence=0.0,
            )

        # Sort matches by appearance position in text
        matches.sort(key=lambda x: x.position)

        if anchor_pos is not None:
            def distance(m: ScaleDetectionResult) -> float:
                diff = m.position - anchor_pos
                if diff >= -500 and diff <= 2000:
                    return abs(diff)  # highest priority
                elif diff < -500:
                    return abs(diff) + 5000  # earlier in document
                else:
                    return abs(diff) + 10000  # later in document

            matches.sort(key=distance)
            return matches[0]

        # By default, return the earliest scale declaration in the text
        return matches[0]

    @classmethod
    def detect_currency(cls, text: str) -> str:
        """
        Detects native document currency from headers, units, or ISO codes.
        Defaults to 'USD' if no specific currency is indicated.
        """
        if not text:
            return "USD"

        # Check primary currency indicators
        for pattern, curr_code in CURRENCY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return curr_code

        return "USD"

    @classmethod
    def parse_inline_scale(cls, value_str: str) -> Tuple[Optional[float], Optional[int], str]:
        """
        Parses inline monetary strings like '$45.2 million', '$2.5 billion', '$800 thousand', 'Rp 10.9 trillion'.
        Returns (raw_numeric_value, multiplier, scale_unit).
        """
        if not value_str or not isinstance(value_str, str):
            return None, None, "unknown"

        clean = value_str.strip().lower()
        match = re.search(
            r"(?:[\$\€\£\¥\₹]|rp\.?|idr|eur|gbp|usd)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(trillion|trillions|t|billion|billions|b|million|millions|m|thousand|thousands|k)\b",
            clean,
        )
        if match:
            num_str = match.group(1).replace(",", "")
            unit_str = match.group(2)
            try:
                num = float(num_str)
                mult = SCALE_MULTIPLIERS.get(unit_str, 1)
                if mult == 1_000_000_000_000:
                    canonical_unit = "trillions"
                elif mult == 1_000_000_000:
                    canonical_unit = "billions"
                elif mult == 1_000_000:
                    canonical_unit = "millions"
                else:
                    canonical_unit = "thousands"
                return num, mult, canonical_unit
            except ValueError:
                pass

        return None, None, "unknown"

    @classmethod
    def get_multiplier(cls, unit: Optional[str]) -> int:
        """Get integer multiplier for a given unit string."""
        if not unit:
            return 1
        return SCALE_MULTIPLIERS.get(unit.strip().lower(), 1)
