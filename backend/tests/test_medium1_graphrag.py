"""
Phase 2 MEDIUM-1: Hybrid GraphRAG Architecture Tests.

Verifies:
  1. SqlRetriever structured metrics retrieval (None values formatted as N/A).
  2. VectorRetriever Pinecone semantic search & Cohere query embedding.
  3. GraphRetriever Neo4j relationship traversal (Borrower -> Facility -> Covenant).
  4. RetrieverFactory hybrid orchestration.
  5. CopilotAgent integration with Hybrid Retriever.
  6. Pinecone unavailable fallback.
  7. Neo4j unavailable fallback.
  8. Both unavailable fallback (SQL-Only mode with limitation notice).
  9. Missing financial metrics handling (no conversion of None -> 0).
 10. Explicit evidence context tagging & anti-hallucination prompt rules.
"""
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock
from ai.rag.retrievers.sql_retriever import SqlRetriever
from ai.rag.retrievers.vector_retriever import VectorRetriever
from ai.rag.retrievers.graph_retriever import GraphRetriever
from ai.rag.retriever_factory import RetrieverFactory
from ai.agents.copilot_agent import CopilotAgent


class MockSessionGraphRAG:
    """Mock session for SQLRetriever testing."""

    def __init__(self, borrower=None, health=None, covenants=None, risk=None, fin=None):
        self.borrower = borrower or {"id": "b1", "company_name": "Acme Corp", "sector": "Tech", "country": "USA", "risk_rating_level": "Moderate", "risk_rating_score": 6.5}
        self.health = health or {"score": 62.0, "category": "moderate", "financial_score": 55.0, "compliance_score": 70.0, "liquidity_score": None, "leverage_score": None, "explanation": "Moderate stress"}
        self.covenants = covenants or [{"status": "breach", "current_value": 4.8, "threshold_value": 4.0, "headroom_pct": -20.0, "reason": "Exceeds max leverage", "covenant_name": "Max Leverage", "covenant_type": "leverage", "threshold_direction": "max"}]
        self.risk = risk or {"default_probability": 22.5, "risk_category": "high", "confidence_score": 0.88, "z_score": 2.3, "risk_factors": '["High Leverage"]'}
        self.fin = fin or {"reporting_period": "FY 10-K", "revenue": 100_000_000, "ebitda": 20_000_000, "net_income": 5_000_000, "total_debt": 96_000_000, "net_debt": 80_000_000, "cash": 16_000_000, "interest_expense": None, "leverage_ratio": 4.8, "interest_coverage": None, "dscr": None}

    async def execute(self, stmt, params=None):
        sql = str(stmt).upper()

        class MockResult:
            def __init__(self, rows):
                self._rows = rows
            def mappings(self):
                return self
            def first(self):
                if isinstance(self._rows, list):
                    return self._rows[0] if self._rows else None
                return self._rows
            def all(self):
                if isinstance(self._rows, list):
                    return self._rows
                return [self._rows] if self._rows else []

        if "FROM BORROWERS" in sql:
            return MockResult(self.borrower)
        elif "FROM BORROWER_HEALTH_SCORES" in sql:
            return MockResult(self.health)
        elif "FROM COVENANT_MONITORING" in sql:
            return MockResult(self.covenants)
        elif "FROM RISK_ASSESSMENTS" in sql:
            return MockResult(self.risk)
        elif "FROM FINANCIAL_METRICS" in sql:
            return MockResult(self.fin)
        return MockResult([])


@pytest.mark.asyncio
async def test_sql_retriever_structured_metrics():
    """Verify SqlRetriever retrieves structured data and formats None as N/A."""
    session = MockSessionGraphRAG()
    retriever = SqlRetriever()
    results = await retriever.retrieve("Why is this borrower high risk?", borrower_id="b1", session=session)

    assert len(results) >= 4
    sources = [r["source"] for r in results]
    assert all(s == "postgres_sql" for s in sources)

    # Check N/A formatting for None fields
    fin_item = next(r for r in results if r["type"] == "financial_metrics")
    assert "Interest Coverage: N/A" in fin_item["content"]
    assert "DSCR: N/A" in fin_item["content"]
    assert "Leverage Ratio: 4.80x" in fin_item["content"]


@pytest.mark.asyncio
async def test_vector_retriever_pinecone():
    """Verify VectorRetriever embeds query via Cohere and queries Pinecone."""
    mock_cohere = MagicMock()
    mock_cohere.embed = AsyncMock(return_value=[[0.1] * 1024])
    mock_cohere.initialize = MagicMock()

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[
        {"id": "c1", "score": 0.89, "metadata": {"page_number": 12, "section": "Section 4.01", "text": "Maximum Leverage Ratio shall not exceed 4.00x."}}
    ])

    retriever = VectorRetriever(pinecone_client=mock_pinecone, cohere_client=mock_cohere)
    results = await retriever.retrieve("What is the leverage covenant threshold?", borrower_id="b1")

    assert len(results) == 1
    assert results[0]["source"] == "pinecone_vector"
    assert "Page 12" in results[0]["content"]
    assert "Maximum Leverage Ratio shall not exceed 4.00x" in results[0]["content"]


@pytest.mark.asyncio
async def test_graph_retriever_neo4j():
    """Verify GraphRetriever queries Neo4j relationship path."""
    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(return_value=[
        {"borrower_name": "Acme Corp", "facility_name": "Senior Term Loan A", "covenant_name": "Max Leverage", "covenant_type": "leverage", "threshold": 4.0}
    ])

    retriever = GraphRetriever(neo4j_client=mock_neo4j)
    results = await retriever.retrieve("Show covenants for borrower", borrower_id="b1")

    assert len(results) == 1
    assert results[0]["source"] == "neo4j_graph"
    assert "Acme Corp ──► Senior Term Loan A ──► Covenant 'Max Leverage'" in results[0]["content"]


@pytest.mark.asyncio
async def test_hybrid_retriever_factory():
    """Verify RetrieverFactory.retrieve_hybrid() orchestrates all 3 retrievers."""
    session = MockSessionGraphRAG()

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[{"id": "v1", "score": 0.85, "metadata": {"text": "Agreement clause"}}])

    mock_cohere = MagicMock()
    mock_cohere.initialize = MagicMock()
    mock_cohere.embed = AsyncMock(return_value=[[0.1] * 1024])

    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(return_value=[{"borrower_name": "Acme", "facility_name": "Revolver", "covenant_name": "DSCR", "covenant_type": "coverage", "threshold": 1.25}])

    factory = RetrieverFactory(neo4j_client=mock_neo4j, pinecone_client=mock_pinecone)
    res = await factory.retrieve_hybrid("Why is borrower high risk?", borrower_id="b1", session=session)

    assert len(res["sql_results"]) >= 4
    assert len(res["graph_results"]) == 1
    assert len(res["vector_results"]) == 1
    assert res["statuses"] == {"sql": True, "graph": True, "vector": True}


@pytest.mark.asyncio
async def test_copilot_using_hybrid_retriever():
    """Verify CopilotAgent invokes RetrieverFactory and passes structured evidence to Cohere."""
    session = MockSessionGraphRAG()

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="**Borrower Risk Summary:**\n- [PostgreSQL] Leverage is **4.80x** vs threshold **4.00x**.\n- [Neo4j] Facility is Senior Term Loan A.\n- [Pinecone] Clause Section 4.01 confirms 4.00x max limit.")

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[{"id": "v1", "score": 0.88, "metadata": {"page_number": 14, "section": "S4.01", "text": "Leverage ratio clause"}}])

    mock_cohere = MagicMock()
    mock_cohere.initialize = MagicMock()
    mock_cohere.embed = AsyncMock(return_value=[[0.1] * 1024])

    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(return_value=[{"borrower_name": "Acme Corp", "facility_name": "Senior Term Loan A", "covenant_name": "Max Leverage", "covenant_type": "leverage", "threshold": 4.0}])

    factory = RetrieverFactory(neo4j_client=mock_neo4j, pinecone_client=mock_pinecone)
    agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=factory)

    state = {
        "user_query": "Why is this borrower high risk?",
        "borrower_id": "b1",
        "session": session
    }
    result = await agent.run(state)

    assert "response" in result
    assert "[PostgreSQL]" not in result["response"]
    assert any("[SOURCE: PostgreSQL Structured Data]" in c for c in result["citations"])
    assert result["evidence_sources"]["sql_count"] >= 4
    assert result["evidence_sources"]["graph_count"] == 1
    assert result["evidence_sources"]["vector_count"] == 1
    assert result["hybrid_retrieval_status"] == {"sql": True, "graph": True, "vector": True}


@pytest.mark.asyncio
async def test_pinecone_unavailable_fallback():
    """Verify Copilot gracefully falls back to Hybrid SQL + Graph when Pinecone is unavailable."""
    session = MockSessionGraphRAG()

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="[PostgreSQL] Health score 62/100. [Neo4j] Max Leverage covenant monitored.")

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[])  # Empty vector matches

    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(return_value=[{"covenant_name": "Max Leverage", "threshold": 4.0}])

    factory = RetrieverFactory(neo4j_client=mock_neo4j, pinecone_client=mock_pinecone)
    agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=factory)

    result = await agent.run({"user_query": "Check risk", "borrower_id": "b1", "session": session})

    assert result["hybrid_retrieval_status"]["vector"] is False
    assert result["hybrid_retrieval_status"]["graph"] is True
    # Citation blocks must include limitation notice
    citations_str = " ".join(result["citations"])
    assert "Hybrid SQL + Graph Mode" in citations_str
    assert "Pinecone vector document search is currently unavailable" in citations_str


@pytest.mark.asyncio
async def test_neo4j_unavailable_fallback():
    """Verify Copilot gracefully falls back to Hybrid SQL + Vector when Neo4j is unavailable."""
    session = MockSessionGraphRAG()

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="[PostgreSQL] Leverage 4.8x. [Pinecone] Passage S4.01.")

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[{"id": "v1", "score": 0.8, "metadata": {"text": "Clause"}}])

    mock_cohere = MagicMock()
    mock_cohere.initialize = MagicMock()
    mock_cohere.embed = AsyncMock(return_value=[[0.1] * 1024])

    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(side_effect=Exception("Neo4j connection refused"))

    factory = RetrieverFactory(neo4j_client=mock_neo4j, pinecone_client=mock_pinecone)
    agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=factory)

    result = await agent.run({"user_query": "Check risk", "borrower_id": "b1", "session": session})

    assert result["hybrid_retrieval_status"]["graph"] is False
    assert result["hybrid_retrieval_status"]["vector"] is True
    citations_str = " ".join(result["citations"])
    assert "Hybrid SQL + Vector Mode" in citations_str
    assert "Neo4j Knowledge Graph traversal is currently unavailable" in citations_str


@pytest.mark.asyncio
async def test_both_unavailable_fallback_sql_only():
    """Verify Copilot gracefully falls back to SQL-Only mode when both Pinecone & Neo4j are down."""
    session = MockSessionGraphRAG()

    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="[PostgreSQL] Leverage 4.8x, Health score 62/100.")

    mock_pinecone = MagicMock()
    mock_pinecone.initialize = MagicMock()
    mock_pinecone.query = AsyncMock(return_value=[])

    mock_neo4j = MagicMock()
    mock_neo4j.initialize = MagicMock()
    mock_neo4j.execute_query = AsyncMock(side_effect=Exception("Neo4j down"))

    factory = RetrieverFactory(neo4j_client=mock_neo4j, pinecone_client=mock_pinecone)
    agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=factory)

    result = await agent.run({"user_query": "Check risk", "borrower_id": "b1", "session": session})

    assert result["hybrid_retrieval_status"]["graph"] is False
    assert result["hybrid_retrieval_status"]["vector"] is False
    assert result["hybrid_retrieval_status"]["sql"] is True
    citations_str = " ".join(result["citations"])
    assert "SQL-Only Mode" in citations_str


@pytest.mark.asyncio
async def test_missing_financial_data_handling():
    """Verify missing metrics remain N/A and do not convert to 0."""
    fin = {"reporting_period": "FY", "revenue": None, "ebitda": None, "interest_expense": None, "leverage_ratio": None, "interest_coverage": None}
    session = MockSessionGraphRAG(fin=fin)

    retriever = SqlRetriever()
    results = await retriever.retrieve("Check financials", borrower_id="b1", session=session)

    fin_item = next(r for r in results if r["type"] == "financial_metrics")
    assert "EBITDA: N/A" in fin_item["content"]
    assert "Leverage Ratio: N/A" in fin_item["content"]
    assert "Interest Coverage: N/A" in fin_item["content"]


@pytest.mark.asyncio
async def test_evidence_context_and_no_hallucination():
    """Verify evidence context passed to Cohere contains explicit source tags and anti-hallucination instructions."""
    session = MockSessionGraphRAG()
    mock_llm = MagicMock()
    mock_llm.generate = AsyncMock(return_value="Synthesized response")

    factory = RetrieverFactory()
    agent = CopilotAgent(llm_provider=mock_llm, retriever_factory=factory)

    await agent.run({"user_query": "Why is this borrower high risk?", "borrower_id": "b1", "session": session})

    # Inspect call args to LLM generate
    assert mock_llm.generate.called
    call_kwargs = mock_llm.generate.call_args.kwargs
    prompt = call_kwargs["prompt"]
    system_prompt = call_kwargs["system_prompt"]

    assert "### [SOURCE: PostgreSQL Structured Data]" in prompt
    assert "### [SOURCE: Neo4j Knowledge Graph]" in prompt
    assert "### [SOURCE: Pinecone Vector Search]" in prompt
    assert "NEVER claim to have retrieved information from a source marked as unavailable" in system_prompt
