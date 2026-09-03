"""
Regression tests for covenant extraction precision and data-lineage integrity.
Ensures non-loan documents and unrelated filings (8-K, executive compensation)
never receive synthetic/hallucinated covenants.
"""
from unittest.mock import AsyncMock, MagicMock
import pytest
from ai.agents.covenant_agent import CovenantAgent


@pytest.fixture
def covenant_agent():
    mock_llm = MagicMock()
    mock_llm.generate_response = AsyncMock(return_value="{}")
    mock_mcp = MagicMock()
    mock_mcp.execute_tool = AsyncMock(return_value={"success": True, "data": []})
    return CovenantAgent(llm_service=mock_llm, mcp_client=mock_mcp)


class TestCovenantExtractionLineage:

    def test_non_loan_sec_filing_with_notes_and_credit_extracts_zero_covenants(self, covenant_agent):
        """Case A: Filing with words 'notes', 'footnotes', 'credit' but no covenant ratios."""
        text = """
        Apple Inc. Form 8-K Current Report.
        Item 8.01 Other Events.
        The Company has issued Senior Notes under its existing credit facility framework.
        Footnotes to the financial statements indicate interest rate terms on the notes.
        """
        covenants = covenant_agent._pattern_extract_covenants(text)
        assert covenants == [], f"Expected zero covenants, but found: {covenants}"

    def test_executive_compensation_8k_disclosure_extracts_zero_covenants(self, covenant_agent):
        """Case B: 8-K executive compensation filing."""
        text = """
        Apple Inc. Form 8-K/A.
        Item 5.02 Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements of Certain Officers.
        On September 1, 2026, the Compensation Committee approved equity incentive awards.
        Restricted stock units are subject to performance vesting criteria over a three-year period.
        """
        covenants = covenant_agent._pattern_extract_covenants(text)
        assert covenants == [], f"Expected zero covenants, but found: {covenants}"

    def test_real_maximum_leverage_ratio_covenant_is_extracted(self, covenant_agent):
        """Case C: Legitimate credit agreement with Maximum Leverage Ratio."""
        text = """
        SECTION 7.11 Financial Covenants.
        (a) Maximum Consolidated Leverage Ratio. The Borrower shall not permit the Consolidated Leverage Ratio
        as of the end of any fiscal quarter to exceed 3.50:1.00.
        """
        covenants = covenant_agent._pattern_extract_covenants(text)
        assert len(covenants) == 1
        assert covenants[0]["name"] == "Maximum Consolidated Leverage Ratio"
        assert covenants[0]["threshold"] == 3.5
        assert covenants[0]["threshold_direction"] == "max"

    def test_real_minimum_interest_coverage_covenant_is_extracted(self, covenant_agent):
        """Case D: Legitimate credit agreement with Minimum Interest Coverage Ratio."""
        text = """
        SECTION 7.11 Financial Covenants.
        (b) Minimum Interest Coverage Ratio. The Borrower shall maintain an Interest Coverage Ratio
        of not less than 3.00:1.00 at the end of each fiscal quarter.
        """
        covenants = covenant_agent._pattern_extract_covenants(text)
        assert len(covenants) == 1
        assert covenants[0]["name"] == "Minimum Interest Coverage Ratio"
        assert covenants[0]["threshold"] == 3.0
        assert covenants[0]["threshold_direction"] == "min"

    def test_document_mentioning_promissory_notes_does_not_invent_covenants(self, covenant_agent):
        """Case E: Term loan and promissory note mentions without covenant formulas."""
        text = """
        The borrower entered into a term loan agreement evidenced by promissory notes.
        All notes mature in 2030 and bear interest at SOFR plus 250 bps.
        """
        covenants = covenant_agent._pattern_extract_covenants(text)
        assert covenants == [], f"Expected zero covenants, but found: {covenants}"
