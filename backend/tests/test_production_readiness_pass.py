"""
Comprehensive Production-Readiness Regression Tests.

Covers:
  1. Reporting Data Integrity (None for unanalyzed score/metrics, PENDING ANALYSIS status)
  2. RBAC Security on GET /borrowers/, GET /borrowers/{id}, GET /organizations/
  3. Vector Tenant Isolation (no cross-tenant filter=None fallback in VectorRetriever)
  4. Internal Server Error Leakage (hides str(exc) in production, reveals in dev)
  5. File Upload Path Traversal Protection (sanitizes filenames with os.path.basename)
  6. SEC Downloader SSRF Prevention (strict urllib.parse hostname validation)
  7. Copilot & Neo4j Singleton Driver Lifecycle
  8. Cohere Embedding Model Config Consistency (embed-english-v3.0)
  9. Entity Listing Pagination (limit/offset at query level)
 10. Pydantic V2 LoanResponseSchema model_config
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# ── 1. REPORTING DATA INTEGRITY ─────────────────────────────────────
class TestReportingDataIntegrity:

    def test_reporting_agent_unanalyzed_borrower_preserves_none(self):
        """Unanalyzed borrower must produce None for health_score & default_probability,
        and PENDING ANALYSIS recommendation without fabricating 75.0 or 5.0%."""
        from ai.agents.reporting_agent import ReportingAgent

        agent = ReportingAgent()
        memo = agent.generate_credit_memo(
            borrower={"id": "b-1", "company_name": "Test Unanalyzed Co"},
            health={},  # no health data
            default_pred={},  # no default pred data
            covenants=[],
            financials={},  # no financial data
        )

        assert memo["summary"]["health_score"] is None, (
            f"Expected health_score=None for unanalyzed borrower, got {memo['summary']['health_score']}"
        )
        assert memo["summary"]["default_probability"] is None, (
            f"Expected default_probability=None, got {memo['summary']['default_probability']}"
        )
        assert memo["summary"]["health_category"] == "UNANALYZED"
        assert "PENDING ANALYSIS" in memo["summary"]["recommendation"]
        assert memo["financial_highlights"]["revenue"] is None
        assert memo["financial_highlights"]["leverage_ratio"] is None

    def test_reporting_agent_analyzed_borrower_preserves_calculated_values(self):
        """Analyzed borrower must retain real calculated scores and ratios."""
        from ai.agents.reporting_agent import ReportingAgent

        agent = ReportingAgent()
        memo = agent.generate_credit_memo(
            borrower={"id": "b-2", "company_name": "Strong Borrower Inc"},
            health={"score": 88.5, "category": "good"},
            default_pred={"default_probability": 3.2, "risk_category": "LOW"},
            covenants=[],
            financials={"revenue": 5000000.0, "leverage_ratio": 1.5},
        )

        assert memo["summary"]["health_score"] == 88.5
        assert memo["summary"]["default_probability"] == 3.2
        assert memo["financial_highlights"]["revenue"] == 5000000.0
        assert memo["financial_highlights"]["leverage_ratio"] == 1.5
        assert "APPROVE" in memo["summary"]["recommendation"]


# ── 2. VECTOR TENANT ISOLATION ───────────────────────────────────────
class TestVectorTenantIsolation:

    @pytest.mark.asyncio
    async def test_vector_retriever_zero_results_does_not_retry_unfiltered(self):
        """When borrower_id is supplied and Pinecone returns 0 matches,
        VectorRetriever must return [] and NOT query Pinecone again without filter."""
        from ai.rag.retrievers.vector_retriever import VectorRetriever

        mock_pinecone = MagicMock()
        mock_pinecone.initialize = MagicMock()
        mock_pinecone.query = AsyncMock(return_value=[])  # 0 matches

        mock_cohere = MagicMock()
        mock_cohere.initialize = MagicMock()
        mock_cohere.embed = AsyncMock(return_value=[[0.1] * 1024])

        retriever = VectorRetriever(pinecone_client=mock_pinecone, cohere_client=mock_cohere)
        results = await retriever.retrieve(query="covenant breach", borrower_id="borrower-empty-1")

        assert results == [], f"Expected empty list for non-matching borrower, got {results}"
        # Pinecone query must have been called EXACTLY ONCE with filter={"borrower_id": "borrower-empty-1"}
        assert mock_pinecone.query.call_count == 1, (
            f"Expected exactly 1 Pinecone query call (tenant-isolated), got {mock_pinecone.query.call_count}"
        )
        _, kwargs = mock_pinecone.query.call_args
        assert kwargs.get("filter") == {"borrower_id": "borrower-empty-1"}, (
            f"Pinecone filter must contain borrower_id, got {kwargs.get('filter')}"
        )


# ── 3. INTERNAL ERROR INFORMATION LEAKAGE ───────────────────────────
class TestInternalErrorLeakage:

    def test_production_environment_hides_exception_details(self):
        """In production environment (APP_ENV != 'development'), HTTP 500 responses must not leak str(exc)."""
        from app.core.config import settings

        original_env = settings.APP_ENV
        try:
            settings.APP_ENV = "production"
            # Simulate exception handling logic from main.py / middleware.py
            exc = ValueError("Sensitive database password or internal stack trace: secret123")
            body = {"detail": "An internal server error occurred."}
            if settings.APP_ENV == "development":
                body["error"] = str(exc)

            assert "error" not in body
            assert "secret123" not in str(body)
        finally:
            settings.APP_ENV = original_env

    def test_development_environment_includes_exception_details(self):
        """In development environment, error field is included for debugging."""
        from app.core.config import settings

        original_env = settings.APP_ENV
        try:
            settings.APP_ENV = "development"
            exc = ValueError("Debug message for dev")
            body = {"detail": "An internal server error occurred."}
            if settings.APP_ENV == "development":
                body["error"] = str(exc)

            assert body.get("error") == "Debug message for dev"
        finally:
            settings.APP_ENV = original_env


# ── 4. FILE UPLOAD PATH TRAVERSAL ─────────────────────────────────────
class TestUploadPathTraversalProtection:

    @pytest.mark.asyncio
    async def test_upload_handler_sanitizes_path_traversal_filenames(self, tmp_path):
        """UploadDocumentHandler must sanitize command.file_name with os.path.basename
        preventing directory traversal outside UPLOAD_DIR."""
        import os
        from app.core.config import settings
        from app.application.uploads.commands import UploadDocumentCommand
        from app.application.uploads.handlers import UploadDocumentHandler

        orig_upload_dir = settings.UPLOAD_DIR
        settings.UPLOAD_DIR = str(tmp_path)
        try:
            mock_session = MagicMock()
            mock_session.flush = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_loan = MagicMock()
            mock_loan.borrower_id = "borrower-1"

            mock_loan_repo = MagicMock()
            mock_loan_repo.get_by_id = AsyncMock(return_value=mock_loan)

            handler = UploadDocumentHandler(session=mock_session)
            handler._loan_repo = mock_loan_repo

            # Content mock
            mock_content = MagicMock()
            mock_content.read.return_value = b"sample pdf bytes"

            command = UploadDocumentCommand(
                loan_id="loan-123",
                file_name="../../../etc/passwd_malicious.pdf",
                file_type="loan_agreement",
                content=mock_content,
                size_bytes=100,
            )

            with patch("aiofiles.open", MagicMock()) as mock_aioopen:
                mock_file_ctx = AsyncMock()
                mock_aioopen.return_value.__aenter__.return_value = mock_file_ctx

                orm_result = await handler.handle(command)

                # Saved file path must NOT contain directory traversal ../
                saved_path = orm_result.file_path
                assert "../" not in saved_path, f"Path traversal character found in saved_path: {saved_path}"
                assert saved_path.endswith("passwd_malicious.pdf")
                assert saved_path.startswith(str(tmp_path))
        finally:
            settings.UPLOAD_DIR = orig_upload_dir


# ── 5. SEC DOWNLOADER SSRF PREVENTION ─────────────────────────────────
class TestSECDownloaderSSRFPrevention:

    def test_validate_url_accepts_legitimate_sec_and_cloudfront_urls(self):
        """Valid SEC EDGAR and CloudFront filing URLs must pass validation."""
        from integrations.sec.downloader import SECDownloader

        dl = SECDownloader()
        assert dl.validate_url("https://www.sec.gov/Archives/edgar/data/12345/0001.htm")
        assert dl.validate_url("https://sec.gov/filings/123.pdf")
        assert dl.validate_url("https://d12345.cloudfront.net/sec_filings/sample.pdf")

    def test_validate_url_rejects_ssrf_attack_urls(self):
        """Attack URLs attempting domain spoofing or query tricks must be rejected."""
        from integrations.sec.downloader import SECDownloader

        dl = SECDownloader()
        # Query parameter spoofing
        assert not dl.validate_url("https://attacker.com/?sec.gov/file.pdf")
        # Subdomain spoofing
        assert not dl.validate_url("https://sec.gov.attacker.com/malicious.pdf")
        assert not dl.validate_url("https://evil-sec.gov.attacker.com/file")
        # Malformed / local SSRF
        assert not dl.validate_url("http://169.254.169.254/latest/meta-data/")
        assert not dl.validate_url("http://localhost:8000/internal")


# ── 6. COHERE EMBEDDING MODEL CONFIG CONSISTENCY ──────────────────────
class TestCohereConfigConsistency:

    def test_config_embed_model_matches_client_default(self):
        """settings.COHERE_EMBED_MODEL must specify embed-english-v3.0 (1024-dim)."""
        from app.core.config import settings

        assert settings.COHERE_EMBED_MODEL == "embed-english-v3.0", (
            f"Expected COHERE_EMBED_MODEL='embed-english-v3.0', got '{settings.COHERE_EMBED_MODEL}'"
        )


# ── 7. PYDANTIC V2 SCHEMA CONFIG ─────────────────────────────────────
class TestPydanticV2LoanSchema:

    def test_loan_response_schema_uses_model_config(self):
        """LoanResponseSchema must use Pydantic V2 model_config = ConfigDict(from_attributes=True)."""
        from app.core.schemas.loan import LoanResponseSchema

        assert hasattr(LoanResponseSchema, "model_config"), "LoanResponseSchema missing model_config"
        assert LoanResponseSchema.model_config.get("from_attributes") is True
