"""
Regression tests for AI Credit Copilot Pipeline & Non-Empty Answer Guarantees.
Verifies that:
- Copilot always returns non-empty answers when evidence is available.
- Response schema adheres to frontend expectations (response, citations, hybrid_retrieval_status).
- Missing/offline Knowledge Graph gracefully falls back to SQL + Vector without breaking.
- Transient LLM errors or empty LLM output trigger evidence-grounded fallback synthesis.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from ai.agents.copilot_agent import CopilotAgent
from ai.rag.retriever_factory import RetrieverFactory
from integrations.cohere.client import CohereClient


class TestCopilotPipeline:

    @pytest.mark.asyncio
    async def test_copilot_response_schema_and_non_empty(self):
        """Test A & B: Copilot returns non-empty response with correct schema."""
        mock_factory = MagicMock(spec=RetrieverFactory)
        mock_factory.retrieve_hybrid = AsyncMock(return_value={
            "sql_results": [
                {"type": "borrower_profile", "content": "Borrower: Apple | Sector: Tech", "metadata": {"company_name": "Apple"}},
                {"type": "covenant_monitoring", "content": "Covenant: Maximum Leverage Ratio | Status: UNKNOWN", "metadata": {"covenant_name": "Maximum Leverage Ratio", "status": "UNKNOWN", "threshold_value": "4.0x"}},
                {"type": "financial_metrics", "content": "Revenue: $109.42B", "metadata": {"revenue": 109417000000.0}},
            ],
            "graph_results": [],
            "vector_results": [{"content": "Document Passage Chunk 1"}],
            "statuses": {"sql": True, "graph": False, "vector": True},
        })

        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="**Covenant Analysis for Apple [PostgreSQL]**: Total 1 covenant found.")

        agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=mock_factory)
        result = await agent.run({
            "user_query": "How many covenants have been found?",
            "borrower_id": "test-borrower-123",
        })

        assert result["query"] == "How many covenants have been found?"
        assert isinstance(result["response"], str)
        assert len(result["response"].strip()) > 0
        assert "citations" in result
        assert len(result["citations"]) > 0
        assert "hybrid_retrieval_status" in result
        assert result["hybrid_retrieval_status"]["sql"] is True
        assert result["hybrid_retrieval_status"]["graph"] is False

    @pytest.mark.asyncio
    async def test_copilot_handles_missing_knowledge_graph_gracefully(self):
        """Test E: Missing/offline Knowledge Graph operates in Hybrid SQL + Vector mode."""
        mock_factory = MagicMock(spec=RetrieverFactory)
        mock_factory.retrieve_hybrid = AsyncMock(return_value={
            "sql_results": [{"type": "borrower_profile", "content": "Borrower: Apple", "metadata": {"company_name": "Apple"}}],
            "graph_results": [],
            "vector_results": [{"content": "Chunk 1"}],
            "statuses": {"sql": True, "graph": False, "vector": True},
        })

        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Apple financial metrics are grounded [PostgreSQL].")

        agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=mock_factory)
        result = await agent.run({"user_query": "Summarize financial metrics.", "borrower_id": "b-1"})

        assert len(result["response"].strip()) > 0
        assert any("LIMITATION NOTICE: Operating in Hybrid SQL + Vector Mode" in c for c in result["citations"])

    @pytest.mark.asyncio
    async def test_copilot_empty_or_failed_llm_triggers_fallback_synthesis(self):
        """Test F: When LLM generation fails or returns empty, fallback synthesis generates non-empty answer."""
        mock_factory = MagicMock(spec=RetrieverFactory)
        mock_factory.retrieve_hybrid = AsyncMock(return_value={
            "sql_results": [
                {"type": "borrower_profile", "content": "Borrower: Apple | Sector: Technology", "metadata": {"company_name": "Apple"}},
                {"type": "covenant_monitoring", "content": "Covenant: Max Leverage | Status: UNKNOWN", "metadata": {"covenant_name": "Max Leverage", "status": "UNKNOWN", "threshold_value": "4.0x"}},
                {"type": "covenant_monitoring", "content": "Covenant: Min Interest Coverage | Status: UNKNOWN", "metadata": {"covenant_name": "Min Interest Coverage", "status": "UNKNOWN", "threshold_value": "2.5x"}},
                {"type": "financial_metrics", "content": "Revenue: $109.42B", "metadata": {"revenue": 109417000000.0, "total_debt": 82350000000.0}},
            ],
            "graph_results": [],
            "vector_results": [],
            "statuses": {"sql": True, "graph": False, "vector": False},
        })

        # LLM returns empty string
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="")

        agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=mock_factory)
        result = await agent.run({
            "user_query": "How many covenants have been found in the company document and how many have been breached?",
            "borrower_id": "b-1",
        })

        # Response must NOT be empty and MUST NOT contain internal source tags
        assert result["response"]
        assert len(result["response"].strip()) > 0
        assert "Apple" in result["response"]
        assert "**Total Covenants Monitored:** 2" in result["response"]
        assert "**Breached:** 0" in result["response"]
        assert "[PostgreSQL]" not in result["response"]
        assert "[Neo4j]" not in result["response"]
        assert "[Pinecone]" not in result["response"]

    @pytest.mark.asyncio
    async def test_cohere_client_retries_on_empty_content(self):
        """Test CohereClient chat retry and non-empty fallback guarantees."""
        client = CohereClient(api_key="test_key")
        mock_async_client = MagicMock()
        # Simulate attempt 1 empty, attempt 2 success
        response_empty = MagicMock()
        response_empty.message.content = []
        response_success = MagicMock()
        mock_text = MagicMock()
        mock_text.text = "Grounded response from Cohere"
        response_success.message.content = [mock_text]
        response_success.usage = None

        mock_async_client.chat = AsyncMock(side_effect=[response_empty, response_success])
        client._client = mock_async_client

        res = await client.chat(message="Test query")
        assert res["text"] == "Grounded response from Cohere"

    @pytest.mark.asyncio
    async def test_response_contains_no_internal_infrastructure_tags(self):
        """Verify that user response has no internal tags while citations retain full provenance."""
        mock_factory = MagicMock(spec=RetrieverFactory)
        mock_factory.retrieve_hybrid = AsyncMock(return_value={
            "sql_results": [
                {"type": "borrower_profile", "content": "Borrower: Apple | Sector: Tech", "metadata": {"company_name": "Apple"}},
                {"type": "financial_metrics", "content": "Revenue: $109.42B", "metadata": {"revenue": 109417000000.0}},
            ],
            "graph_results": [],
            "vector_results": [{"content": "Agreement excerpt"}],
            "statuses": {"sql": True, "graph": False, "vector": True},
        })

        # LLM returns text with internal tags
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(return_value="Apple revenue is $109.42B [PostgreSQL]. [Neo4j] graph was offline. [Pinecone] passages analyzed.")

        agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=mock_factory)
        result = await agent.run({
            "user_query": "Summarize Apple credit profile.",
            "borrower_id": "b-1",
        })

        # 1. Response must be clean
        assert "[PostgreSQL]" not in result["response"]
        assert "[Neo4j]" not in result["response"]
        assert "[Pinecone]" not in result["response"]
        assert "[SOURCE:" not in result["response"]
        assert "Apple revenue is $109.42B" in result["response"]

        # 2. Citations must preserve complete provenance
        assert len(result["citations"]) > 0
        assert any("[SOURCE: PostgreSQL Structured Data]" in c for c in result["citations"])
        assert any("[SOURCE: Pinecone Vector Search]" in c for c in result["citations"])
        assert any("LIMITATION NOTICE" in c for c in result["citations"])
