"""
Regression tests for SEC HTML / Inline-XBRL financial statement extraction,
table parsing, scale detection, total revenue disambiguation, and deterministic normalization.
"""
import pytest
import os
import tempfile

from integrations.llamaparse.client import LlamaParseClient
from ai.agents.financial_agent import FinancialAgent
from ai.extraction.scale_detector import ScaleDetector
from ai.extraction.financial_normalizer import FinancialExtractionNormalizer


class TestSECHTMLFinancialExtraction:

    @pytest.mark.asyncio
    async def test_1_html_cleanup_and_table_structure(self):
        """TEST 1: HTML cleanup removes scripts/styles and preserves table row/column text."""
        raw_html = """
        <html>
        <head>
            <style>body { font-family: Arial; } .header { color: red; }</style>
            <script>console.log("ignore me");</script>
        </head>
        <body>
            <p>Header text</p>
            <table>
                <tr><td>CONSOLIDATED STATEMENTS OF OPERATIONS</td></tr>
                <tr><td>(In thousands, except per share data)</td></tr>
                <tr><td>Total revenues</td><td>100,233</td></tr>
            </table>
        </body>
        </html>
        """
        with tempfile.NamedTemporaryFile(suffix=".html", mode="w", delete=False) as f:
            f.write(raw_html)
            tmp_path = f.name

        try:
            parser = LlamaParseClient("not_set")
            res = await parser.parse_document(tmp_path)
            text = res["text"]

            assert "console.log" not in text
            assert "font-family" not in text
            assert "CONSOLIDATED STATEMENTS OF OPERATIONS" in text
            assert "(In thousands, except per share data)" in text
            assert "Total revenues | 100,233" in text or "Total revenues" in text
            assert "100,233" in text
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_2_financial_context_selection_anchors(self):
        """TEST 2: FinancialAgent context selection captures statements and ignores HTML head/TOC noise."""
        head_noise = "CSS_AND_XML_METADATA_NOISE " * 800  # 20k chars of noise
        toc_noise = "\n\nINDEX TO FORM 10-Q\nItem 1. Financial Statements\nConsolidated Statements of Operations ... Page 4\n\n"
        statement = """
        FORRESTER RESEARCH, INC.
        CONSOLIDATED STATEMENTS OF OPERATIONS
        (In thousands, except per share data, unaudited)
        Three Months Ended June 30, 2026:
        Research | $ | 71,708
        Consulting | 20,042
        Events | 8,483
        Total revenues | 100,233
        Total operating expenses | 96,835
        Income (loss) from operations | 3,398
        Interest expense | ( 386 )
        Net income (loss) | $ | 15,253
        """
        full_doc = head_noise + toc_noise + statement

        agent = FinancialAgent(None, None)
        ctx = agent._select_financial_context(full_doc, max_chars=15000)

        assert "CONSOLIDATED STATEMENTS OF OPERATIONS" in ctx
        assert "(In thousands" in ctx
        assert "Total revenues" in ctx
        assert "100,233" in ctx
        # Confirm it didn't just grab the front noise
        assert ctx.startswith("CSS_AND_XML_METADATA_NOISE") is False

    def test_3_thousands_scaling(self):
        """TEST 3: Scale unit 'thousands' deterministically multiplies raw integer by 1,000."""
        context = """
        CONSOLIDATED STATEMENTS OF OPERATIONS
        (In thousands, except per share data)
        Total revenues | 100,233
        Net income | 15,253
        """
        raw_extraction = {
            "reporting_period": "Three Months Ended June 30, 2026",
            "currency": "USD",
            "scale_unit": "thousands",
            "revenue": {"raw_value": 100233, "scale_unit": "thousands"},
            "ebitda": None,
            "net_income": {"raw_value": 15253, "scale_unit": "thousands"},
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }

        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)

        assert norm["revenue"] == 100233000.0
        assert norm["net_income"] == 15253000.0
        meta = norm["extraction_metadata"]
        assert meta["metrics"]["revenue"]["raw_value"] == 100233.0
        assert meta["metrics"]["revenue"]["scale_multiplier"] == 1000
        assert meta["metrics"]["revenue"]["scale_unit"] == "thousands"

    def test_4_millions_scaling_apple(self):
        """TEST 4: Scale unit 'millions' deterministically multiplies raw integer by 1,000,000."""
        context = """
        Apple Inc.
        CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (In millions)
        Total net sales 109,417
        Operating income 35,695
        """
        raw_extraction = {
            "reporting_period": "Three Months Ended June 27, 2026",
            "currency": "USD",
            "scale_unit": "millions",
            "revenue": {"raw_value": 109417, "scale_unit": "millions"},
            "ebitda": {"raw_value": 35695, "scale_unit": "millions"},
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }

        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)

        assert norm["revenue"] == 109417000000.0
        assert norm["ebitda"] == 35695000000.0

    def test_5_billions_scaling(self):
        """TEST 5: Scale unit 'billions' deterministically multiplies raw decimal by 1,000,000,000."""
        context = "STATEMENT OF REVENUES (In billions)\nRevenue: 109.4"
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

    def test_6_conflicting_scale_declarations_position_precedence(self):
        """
        TEST 6: Position-aware scale detection prioritizes statement scale over other sections.
        """
        statement_text = """
        FORRESTER RESEARCH, INC.
        CONSOLIDATED STATEMENTS OF OPERATIONS
        (In thousands, except per share data, unaudited)
        Total revenues | 100,233
        """
        scale_res = ScaleDetector.detect_table_scale(statement_text)
        assert scale_res.scale_unit == "thousands"
        assert scale_res.scale_multiplier == 1000

        raw_extraction = {
            "reporting_period": "Three Months Ended June 30, 2026",
            "currency": "USD",
            "scale_unit": "thousands",
            "revenue": {"raw_value": 100233, "scale_unit": "thousands"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=statement_text)
        assert norm["revenue"] == 100233000.0

    def test_7_segment_vs_total_revenues_disambiguation(self):
        """
        TEST 7: When segment lines (Research, Consulting, Events) and Total revenues exist,
        Total revenues (100,233) must be chosen.
        """
        context = """
        CONSOLIDATED STATEMENTS OF OPERATIONS
        (In thousands)
        Revenues:
        Research | $ | 71,708
        Consulting | 20,042
        Events | 8,483
        Total revenues | 100,233
        """
        agent = FinancialAgent(None, None)
        extracted = agent._pattern_extract_financials(context)

        assert extracted["revenue"]["raw_value"] == 100233.0
        assert extracted["revenue"]["raw_value"] != 71708.0

        norm = FinancialExtractionNormalizer.normalize(extracted, context_text=context)
        assert norm["revenue"] == 100233000.0

    def test_8_none_not_equal_zero_invariant(self):
        """TEST 8: Missing metrics remain None, never converted to 0.0."""
        context = "CONSOLIDATED STATEMENTS OF OPERATIONS\n(In thousands)\nTotal revenues | 100,233"
        raw_extraction = {
            "reporting_period": "Q2 2026",
            "currency": "USD",
            "revenue": {"raw_value": 100233, "scale_unit": "thousands"},
            "ebitda": None,
            "net_income": None,
            "total_debt": None,
            "cash": None,
            "interest_expense": None,
        }
        norm = FinancialExtractionNormalizer.normalize(raw_extraction, context_text=context)
        assert norm["revenue"] == 100233000.0
        assert norm["ebitda"] is None
        assert norm["net_income"] is None
        assert norm["total_debt"] is None
        assert norm["cash"] is None
        assert norm["interest_expense"] is None
        assert norm["leverage_ratio"] is None
        assert norm["interest_coverage"] is None

    def test_9_repeated_extraction_determinism(self):
        """TEST 9: Repeated runs produce 100% identical outputs."""
        context = """
        FORRESTER RESEARCH, INC.
        CONSOLIDATED STATEMENTS OF OPERATIONS
        (In thousands, except per share data, unaudited)
        Total revenues | 100,233
        Income (loss) from operations | 3,398
        Net income (loss) | 15,253
        """
        agent = FinancialAgent(None, None)
        r1 = agent._pattern_extract_financials(context)
        r2 = agent._pattern_extract_financials(context)

        n1 = FinancialExtractionNormalizer.normalize(r1, context_text=context)
        n2 = FinancialExtractionNormalizer.normalize(r2, context_text=context)

        assert n1["revenue"] == n2["revenue"] == 100233000.0
        assert n1["ebitda"] == n2["ebitda"] == 3398000.0
        assert n1["net_income"] == n2["net_income"] == 15253000.0
        assert n1["extraction_metadata"] == n2["extraction_metadata"]

    @pytest.mark.asyncio
    async def test_10_forrester_sec_html_full_pipeline(self):
        """
        TEST 10: End-to-end verification of Forrester Form 10-Q filing.
        Asserts raw_value == 100233, scale_unit == thousands, normalized_value == 100233000.0 ($100.2M).
        """
        html_file = "/tmp/covenexa_sec/sec_filing_52218926.html"
        if not os.path.exists(html_file):
            pytest.skip("Forrester test HTML not downloaded in /tmp/covenexa_sec")

        parser = LlamaParseClient("not_set")
        parsed = await parser.parse_document(html_file)
        clean_text = parsed["text"]

        agent = FinancialAgent(None, None)
        ctx = agent._select_financial_context(clean_text)

        assert "CONSOLIDATED STAT" in ctx
        assert "(In thousands" in ctx
        assert "Total revenues" in ctx
        assert "100,233" in ctx

        extracted = agent._pattern_extract_financials(ctx)
        assert extracted["revenue"]["raw_value"] == 100233.0
        assert extracted["revenue"]["scale_unit"] == "thousands"

        norm = FinancialExtractionNormalizer.normalize(extracted, context_text=ctx)
        assert norm["revenue"] == 100233000.0
        assert norm["net_income"] == 15253000.0

    def test_11_sec_html_parser_normal_lxml(self):
        """TEST 11: SECHTMLParser successfully parses HTML with lxml."""
        from integrations.sec.html_parser import SECHTMLParser
        parser = SECHTMLParser()
        html = "<html><body><h1>Item 1.01</h1><p>Credit Agreement terms.</p></body></html>"
        text = parser.parse_html(html)
        assert "Item 1.01" in text
        assert "Credit Agreement terms." in text

    def test_12_sec_html_parser_fallback_on_feature_not_found(self):
        """TEST 12: SECHTMLParser gracefully falls back to html.parser when FeatureNotFound is raised."""
        from unittest.mock import patch
        from bs4 import BeautifulSoup, FeatureNotFound
        from integrations.sec.html_parser import SECHTMLParser

        parser = SECHTMLParser()
        html = "<html><body><h1>SEC 8-K Disclosure</h1><p>Filing details.</p></body></html>"

        orig_init = BeautifulSoup.__init__

        def mock_init(self, markup="", features=None, **kwargs):
            if features == "lxml":
                raise FeatureNotFound("Couldn't find tree builder: lxml")
            return orig_init(self, markup, features=features, **kwargs)

        with patch.object(BeautifulSoup, "__init__", side_effect=mock_init, autospec=True):
            text = parser.parse_html(html)
            assert "SEC 8-K Disclosure" in text
            assert "Filing details." in text

