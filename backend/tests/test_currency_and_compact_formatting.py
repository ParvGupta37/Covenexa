"""
Regression tests for Multi-Currency Detection, Trillion-scale Normalization,
and Non-USD Compact Formatting (e.g. IDR, EUR, GBP, USD).
"""
import pytest

from ai.extraction.scale_detector import ScaleDetector
from ai.extraction.financial_normalizer import FinancialExtractionNormalizer
from ai.extraction.validator import FinancialExtractionValidator
from ai.agents.financial_agent import FinancialAgent


class TestCurrencyAndCompactFormatting:

    def test_currency_detection_indonesian_rupiah(self):
        """Detects IDR from '(in billions of Rupiah)' or 'PT Telkom Indonesia' text."""
        text = """
        PT TELKOM INDONESIA (PERSERO) Tbk AND ITS SUBSIDIARIES
        CONSOLIDATED STATEMENTS OF PROFIT OR LOSS AND OTHER COMPREHENSIVE INCOME
        (Expressed in billions of Rupiah, except per share data)
        Revenues:
        Total revenues | 10,930.7
        """
        curr = ScaleDetector.detect_currency(text)
        assert curr == "IDR"

        scale = ScaleDetector.detect_table_scale(text)
        assert scale.scale_unit == "billions"
        assert scale.scale_multiplier == 1_000_000_000

    def test_currency_detection_euro_gbp_jpy_inr(self):
        """Detects EUR, GBP, JPY, INR from headers and symbols."""
        assert ScaleDetector.detect_currency("CONSOLIDATED STATEMENT OF OPERATIONS (in millions of Euros)") == "EUR"
        assert ScaleDetector.detect_currency("FINANCIAL STATEMENTS (€ in thousands)") == "EUR"
        assert ScaleDetector.detect_currency("STATEMENTS OF INCOME (in millions of Pounds sterling)") == "GBP"
        assert ScaleDetector.detect_currency("FINANCIAL REPORT (£ in thousands)") == "GBP"
        assert ScaleDetector.detect_currency("OPERATIONS REPORT (in billions of Yen)") == "JPY"
        assert ScaleDetector.detect_currency("INCOME STATEMENT (₹ in crores / Lakhs of Rupees)") == "INR"

    def test_telkom_indonesia_trillion_rupiah_normalization(self):
        """
        Telkom Indonesia scenario:
        '10,930.7 billion Rupiah'
        Normalized value = 10,930.7 * 1,000,000,000 = 10,930,700,000,000 IDR.
        No FX conversion performed.
        """
        context = """
        PT TELKOM INDONESIA (PERSERO) Tbk
        CONSOLIDATED STATEMENTS OF PROFIT OR LOSS
        (Expressed in billions of Rupiah)
        Three Months Ended March 31, 2026
        Total revenues | 10,930.7
        Operating profit | 3,120.5
        Net income | 2,450.0
        """
        agent = FinancialAgent(None, None)
        extracted = agent._pattern_extract_financials(context)

        assert extracted["currency"] == "IDR"
        assert extracted["scale_unit"] == "billions"
        assert extracted["revenue"]["raw_value"] == 10930.7

        norm = FinancialExtractionNormalizer.normalize(extracted, context_text=context)

        assert norm["currency"] == "IDR"
        assert norm["revenue"] == 10930700000000.0  # 10.93 Trillion IDR
        assert norm["ebitda"] == 3120500000000.0
        assert norm["net_income"] == 2450000000000.0

        meta = norm["extraction_metadata"]
        assert meta["metrics"]["revenue"]["currency"] == "IDR"
        assert meta["metrics"]["revenue"]["scale_multiplier"] == 1_000_000_000
        assert meta["metrics"]["revenue"]["normalized_value"] == 10930700000000.0

    def test_trillion_scale_parsing(self):
        """Test inline trillion parsing: 'Rp 10.9 trillion' -> 10,900,000,000,000."""
        val, mult, unit = ScaleDetector.parse_inline_scale("Rp 10.9 trillion")
        assert val == 10.9
        assert mult == 1_000_000_000_000
        assert unit == "trillions"

    def test_validator_accepts_idr_and_large_currencies(self):
        """Validator accepts valid ISO currencies including IDR and does not flag errors."""
        payload = {
            "currency": "IDR",
            "reporting_period": "Q1 2026",
            "metrics": {
                "revenue": {
                    "raw_value": 10930.7,
                    "normalized_value": 10930700000000.0,
                    "scale_multiplier": 1_000_000_000,
                    "scale_unit": "billions",
                    "currency": "IDR",
                }
            }
        }
        issues = FinancialExtractionValidator.validate(payload)
        assert len(issues) == 0
