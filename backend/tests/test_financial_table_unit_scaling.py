"""
Regression test suite for Financial Table Unit Normalization & Extraction Hardening.
Verifies SEC table scale detection (millions, thousands, billions), inline expressions,
Total vs Segment disambiguation, None != 0 invariant, and deterministic normalization.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from ai.extraction.scale_detector import ScaleDetector
from ai.extraction.financial_normalizer import FinancialExtractionNormalizer
from ai.extraction.validator import FinancialExtractionValidator
from ai.agents.financial_agent import FinancialAgent


class TestTableScaleDetector:

    def test_detect_millions_sec_header(self):
        text = "Apple Inc. CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (In millions, except per-share amounts)"
        result = ScaleDetector.detect_table_scale(text)
        assert result.scale_unit == "millions"
        assert result.scale_multiplier == 1_000_000

    def test_detect_thousands_sec_header(self):
        text = "CONSOLIDATED STATEMENTS OF INCOME (In thousands, except per share data)"
        result = ScaleDetector.detect_table_scale(text)
        assert result.scale_unit == "thousands"
        assert result.scale_multiplier == 1_000

    def test_detect_billions_sec_header(self):
        text = "STATEMENT OF REVENUE AND EXPENSES (Amounts in billions)"
        result = ScaleDetector.detect_table_scale(text)
        assert result.scale_unit == "billions"
        assert result.scale_multiplier == 1_000_000_000

    def test_detect_dollars_in_millions(self):
        text = "Segment Operating Performance ($ in millions):"
        result = ScaleDetector.detect_table_scale(text)
        assert result.scale_unit == "millions"
        assert result.scale_multiplier == 1_000_000

    def test_inline_scale_parsing(self):
        val, mult, unit = ScaleDetector.parse_inline_scale("$45.2 million")
        assert val == 45.2
        assert mult == 1_000_000
        assert unit == "millions"

        val, mult, unit = ScaleDetector.parse_inline_scale("$2.5 billion")
        assert val == 2.5
        assert mult == 1_000_000_000
        assert unit == "billions"

        val, mult, unit = ScaleDetector.parse_inline_scale("$800 thousand")
        assert val == 800.0
        assert mult == 1_000
        assert unit == "thousands"


class TestFinancialExtractionNormalizer:

    def test_sec_table_in_millions_apple_case(self):
        """
        Scenario A & Important Regression Test:
        '(In millions)' + 'Total net sales: 109,417'
        Must normalize to 109,417,000,000.0. Rejects 109417 and 109417000.
        """
        context = """
        Apple Inc.
        CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (In millions, except per-share amounts)
        Three Months Ended June 27, 2026
        Net sales:
           Products $ 78,678
           Services 30,739
        Total net sales 109,417
        Operating income 35,695
        Net income 29,789
        """
        raw_extraction = {
            "reporting_period": "Three Months Ended June 27, 2026",
            "currency": "USD",
            "scale_unit": "millions",
            "revenue": {"raw_value": 109417, "scale_unit": "millions"},
            "ebitda": {"raw_value": 35695, "scale_unit": "millions"},
            "net_income": {"raw_value": 29789, "scale_unit": "millions"},
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }

        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)

        # Assert correct billions normalization
        assert norm["revenue"] == 109417000000.0
        assert norm["revenue"] != 109417.0
        assert norm["revenue"] != 109417000.0
        assert norm["ebitda"] == 35695000000.0
        assert norm["net_income"] == 29789000000.0

        # Provenance metadata preserved
        meta = norm["extraction_metadata"]
        assert meta["detected_table_scale"]["unit"] == "millions"
        assert meta["detected_table_scale"]["multiplier"] == 1_000_000
        assert meta["metrics"]["revenue"]["raw_value"] == 109417.0
        assert meta["metrics"]["revenue"]["scale_multiplier"] == 1_000_000
        assert meta["metrics"]["revenue"]["normalized_value"] == 109417000000.0

    def test_sec_table_in_thousands(self):
        """Scenario B: '(In thousands)' + 'Revenue: 850,000' -> 850,000,000.0"""
        context = "STATEMENT OF OPERATIONS (In thousands)\nRevenue: 850,000"
        raw_extraction = {
            "reporting_period": "FY 2025",
            "currency": "USD",
            "scale_unit": "thousands",
            "revenue": {"raw_value": 850000, "scale_unit": "thousands"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)
        assert norm["revenue"] == 850000000.0

    def test_sec_table_in_billions(self):
        """Scenario C: '(In billions)' + 'Revenue: 109.4' -> 109,400,000,000.0"""
        context = "STATEMENT OF REVENUE (In billions)\nRevenue: 109.4"
        raw_extraction = {
            "reporting_period": "Q3 2026",
            "currency": "USD",
            "scale_unit": "billions",
            "revenue": {"raw_value": 109.4, "scale_unit": "billions"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)
        assert norm["revenue"] == 109400000000.0

    def test_inline_million_and_billion_values(self):
        """Scenarios D & E: '$45.2 million' -> 45200000 and '$2.5 billion' -> 2500000000"""
        raw_extraction = {
            "reporting_period": "Q2 2025",
            "currency": "USD",
            "revenue": "$45.2 million",
            "ebitda": "$2.5 billion",
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text="")
        assert norm["revenue"] == 45200000.0
        assert norm["ebitda"] == 2500000000.0

    def test_products_vs_total_net_sales_disambiguation(self):
        """
        Scenario F:
        Products = 78,678
        Services = 30,739
        Total net sales = 109,417
        (In millions)
        Revenue must normalize to 109417000000 (NOT 78678000000).
        """
        context = """
        CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (In millions)
        Net sales:
           Products $ 78,678
           Services 30,739
        Total net sales 109,417
        """
        # Even if raw extraction erroneously picked Products (78678)
        raw_extraction = {
            "reporting_period": "Q3 2026",
            "currency": "USD",
            "revenue": {"raw_value": 78678, "scale_unit": "millions"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)
        assert norm["revenue"] == 109417000000.0
        assert norm["revenue"] != 78678000000.0

    def test_none_not_equal_to_zero_invariant(self):
        """Scenario H: Missing values remain None/null, never 0.0"""
        raw_extraction = {
            "reporting_period": "Q3 2026",
            "currency": "USD",
            "revenue": 1000000.0,
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text="")
        assert norm["revenue"] == 1000000.0
        assert norm["ebitda"] is None
        assert norm["net_income"] is None
        assert norm["total_debt"] is None
        assert norm["interest_expense"] is None
        assert norm["leverage_ratio"] is None
        assert norm["interest_coverage"] is None

    def test_repeated_upload_deterministic_consistency(self):
        """Scenario I: Multiple repeated normalizations yield 100% identical outputs."""
        context = "STATEMENT OF OPERATIONS (In millions)\nTotal net sales: 109,417"
        raw_extraction = {
            "reporting_period": "Q3 2026",
            "currency": "USD",
            "scale_unit": "millions",
            "revenue": {"raw_value": 109417, "scale_unit": "millions"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }

        run_1 = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)
        run_2 = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)

        assert run_1["revenue"] == run_2["revenue"] == 109417000000.0
        assert run_1["extraction_metadata"] == run_2["extraction_metadata"]


class TestFinancialExtractionValidator:

    def test_detects_scale_not_applied_error(self):
        payload = {
            "currency": "USD",
            "reporting_period": "Q3 2026",
            "metrics": {
                "revenue": {
                    "raw_value": 109417.0,
                    "normalized_value": 109417.0,  # FAILED to multiply by 1e6
                    "scale_multiplier": 1_000_000,
                    "scale_unit": "millions",
                }
            }
        }
        issues = FinancialExtractionValidator.validate(payload)
        error_types = [i.issue_type for i in issues]
        assert "scale_not_applied" in error_types

    def test_detects_negative_revenue(self):
        payload = {
            "currency": "USD",
            "reporting_period": "Q3 2026",
            "metrics": {
                "revenue": {
                    "raw_value": -500.0,
                    "normalized_value": -500000000.0,
                    "scale_multiplier": 1_000_000,
                    "scale_unit": "millions",
                }
            }
        }
        issues = FinancialExtractionValidator.validate(payload)
        error_types = [i.issue_type for i in issues]
        assert "negative_revenue" in error_types


class TestFinancialAgentPipeline:

    @pytest.mark.asyncio
    async def test_pattern_extractor_with_scale_detection(self):
        """Pattern fallback extractor deterministically detects table scale and normalizes."""
        text = """
        Apple Inc.
        CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)
        (In millions, except number of shares, which are reflected in thousands, and per-share amounts)
        Three Months Ended June 27, 2026
        Net sales:
           Products $ 78,678
           Services 30,739
        Total net sales 109,417
        Operating income 35,695
        Net income 29,789
        """
        agent = FinancialAgent(None, None)
        extracted = agent._pattern_extract_financials(text)

        assert extracted["revenue"]["raw_value"] == 109417.0
        assert extracted["revenue"]["scale_unit"] == "millions"

        normalized = FinancialExtractionNormalizer.normalize(extracted, context_text=text)
        assert normalized["revenue"] == 109417000000.0
        assert normalized["ebitda"] == 35695000000.0
        assert normalized["net_income"] == 29789000000.0
