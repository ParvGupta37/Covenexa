"""
Automated unit & integration tests for CRITICAL-1 through CRITICAL-4 fixes.
"""
import pytest
import uuid
from datetime import date, timedelta
from decimal import Decimal

from app.application.loans.commands import CreateLoanCommand
from app.application.loans.handlers import CreateLoanHandler
from app.core.schemas.loan import LoanCreateSchema, MoneySchema
from app.domain.entities.loan import LoanStatus
from ai.agents.copilot_agent import CopilotAgent, _safe_money, _safe_ratio, _safe_num, _safe_str
from integrations.sec.pipeline import SECDocumentPipeline


@pytest.mark.asyncio
async def test_safe_format_helpers_with_none_values():
    """Verify CRITICAL-3 helper functions handle None and invalid values safely."""
    assert _safe_money(None) == "N/A"
    assert _safe_money(1000000.5) == "$1,000,000.50"
    assert _safe_money("invalid") == "N/A"

    assert _safe_ratio(None) == "N/A"
    assert _safe_ratio(3.5) == "3.50x"
    assert _safe_ratio("invalid") == "N/A"

    assert _safe_num(None) == "N/A"
    assert _safe_num(85.34, "%") == "85.3%"
    assert _safe_num("invalid") == "N/A"

    assert _safe_str(None, "DefaultVal") == "DefaultVal"
    assert _safe_str("  ", "DefaultVal") == "DefaultVal"
    assert _safe_str("Acme Corp") == "Acme Corp"


@pytest.mark.asyncio
async def test_copilot_agent_handles_missing_session_and_none_fields():
    """Verify CRITICAL-3 CopilotAgent does not crash when fields or context are None/missing."""
    from unittest.mock import AsyncMock
    agent = CopilotAgent()
    agent._llm.generate = AsyncMock(return_value="Leverage ratio is calculated from debt and EBITDA.")
    # Test with no session or borrower_id
    result = await agent.run({
        "user_query": "What is the leverage ratio?",
        "borrower_id": None,
        "session": None,
    })
    assert result["query"] == "What is the leverage ratio?"
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_create_loan_schema_optional_agreement_id():
    """Verify CRITICAL-2 LoanCreateSchema accepts optional agreement_id."""
    today = date.today()
    maturity = today + timedelta(days=365 * 5)
    
    # Payload without agreement_id
    payload = LoanCreateSchema(
        borrower_id=str(uuid.uuid4()),
        principal_amount=MoneySchema(amount=Decimal("50000000.0"), currency="USD"),
        interest_rate=0.065,
        start_date=today,
        maturity_date=maturity,
        status=LoanStatus.ACTIVE,
    )
    assert payload.agreement_id is None
    assert payload.principal_amount.amount == Decimal("50000000.0")
    assert payload.interest_rate == 0.065


@pytest.mark.asyncio
async def test_sec_pipeline_invalid_loan_id_raises_value_error(mocker=None):
    """Verify CRITICAL-4 SEC pipeline raises ValueError on invalid loan facility ID."""
    pipeline = SECDocumentPipeline()
    
    class MockSession:
        async def execute(self, statement, params=None):
            class MockResult:
                def mappings(self):
                    class MockMapping:
                        def first(self):
                            return None
                    return MockMapping()
            return MockResult()

    class MockDownloader:
        async def download_filing(self, url):
            return ("/tmp/fake.html", {"cik": "12345"})

    class MockParser:
        def parse_html_file(self, path):
            return "Fake HTML Text"

    pipeline.downloader = MockDownloader()
    pipeline.parser = MockParser()

    with pytest.raises(ValueError, match="Loan facility 'invalid_loan_id' not found"):
        await pipeline.process_sec_url(
            session=MockSession(),
            sec_url="https://www.sec.gov/Archives/edgar/data/123/000.htm",
            loan_id="invalid_loan_id"
        )
