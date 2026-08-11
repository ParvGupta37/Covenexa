"""
AI Copilot Agent — Sprint 4 (Phase 2 MEDIUM-1: Hybrid GraphRAG).
Answers conversational credit risk questions using active Hybrid GraphRAG:
- Structured Credit Risk & Financial Metrics (PostgreSQL SQLRetriever)
- Semantic Document Passages (Pinecone VectorRetriever with Cohere Embed)
- Knowledge Graph Traversal (Neo4j GraphRetriever)
- Cohere Command A Synthesis with strict source citation & evidence grounding
"""
from __future__ import annotations

import structlog
from typing import Dict, Any, List, Optional

from ai.agents.base_agent import BaseAgent
from ai.llm.cohere_provider import CohereProvider
from ai.rag.retriever_factory import RetrieverFactory
from app.core.config import settings

logger = structlog.get_logger(__name__)


def _safe_money(val: Any) -> str:
    if val is None:
        return "N/A"
    try:
        return f"${float(val):,.2f}"
    except (ValueError, TypeError):
        return "N/A"


def _safe_ratio(val: Any) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.2f}x"
    except (ValueError, TypeError):
        return "N/A"


def _safe_num(val: Any, unit: str = "") -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.1f}{unit}"
    except (ValueError, TypeError):
        return "N/A"


def _safe_str(val: Any, default: str = "N/A") -> str:
    if val is None:
        return default
    s = str(val).strip()
    return s if s else default


COPILOT_SYSTEM_PROMPT = """
You are Covenexa AI Copilot — an expert AI Credit Analyst and Risk Officer for Private Credit portfolios.
Answer user questions accurately, concisely, and professionally using ONLY the provided evidence context from PostgreSQL [PostgreSQL], Neo4j [Neo4j], and Pinecone [Pinecone].

Rules:
1. Always cite evidence source tags (e.g., [PostgreSQL], [Neo4j], or [Pinecone]) when stating specific facts, numbers, or covenant clauses.
2. Format response in clean markdown with bullet points and bold highlights.
3. If data or a data source is marked as unavailable or missing, state clearly: "Insufficient data to determine this" for that aspect and explain what data is missing.
4. NEVER claim to have retrieved information from a source marked as unavailable or missing.
5. Provide actionable insights for credit risk decision-makers based on retrieved evidence.
"""


class CopilotAgent(BaseAgent):
    """Hybrid GraphRAG Credit Copilot Agent."""

    def __init__(
        self,
        llm_provider: CohereProvider | None = None,
        retriever_factory: RetrieverFactory | None = None,
    ) -> None:
        self._llm = llm_provider or CohereProvider(api_key=settings.COHERE_API_KEY)
        self._factory = retriever_factory or RetrieverFactory()

    @property
    def name(self) -> str:
        return "CopilotAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes query using active Hybrid GraphRAG (SQL + Graph + Vector)
        and synthesizes a grounded Cohere response with explicit evidence sources.
        """
        user_query = state.get("user_query", "")
        borrower_id = state.get("borrower_id")
        session = state.get("session")

        logger.info("copilot_agent.query", query=user_query, borrower_id=borrower_id)

        # 1. Execute Hybrid RAG retrieval across SQL, Vector, and Graph
        hybrid_res = await self._factory.retrieve_hybrid(
            query=user_query,
            limit=5,
            borrower_id=borrower_id,
            session=session,
        )

        sql_items = hybrid_res.get("sql_results", [])
        graph_items = hybrid_res.get("graph_results", [])
        vector_items = hybrid_res.get("vector_results", [])
        statuses = hybrid_res.get("statuses", {})

        # 2. Build structured evidence context blocks
        context_blocks: List[str] = []

        # ── PostgreSQL Structured Data Source ─────────────────────────────
        if sql_items:
            sql_lines = [f"- {item.get('content')}" for item in sql_items]
            context_blocks.append(
                f"### [SOURCE: PostgreSQL Structured Data]\n" + "\n".join(sql_lines)
            )
        else:
            context_blocks.append(
                "### [SOURCE: PostgreSQL Structured Data]\n"
                "Status: No structured borrower metrics or covenant records found in PostgreSQL."
            )

        # ── Neo4j Knowledge Graph Source ─────────────────────────────────
        if graph_items:
            graph_lines = [f"- {item.get('content')}" for item in graph_items]
            context_blocks.append(
                f"### [SOURCE: Neo4j Knowledge Graph]\n" + "\n".join(graph_lines)
            )
        else:
            context_blocks.append(
                "### [SOURCE: Neo4j Knowledge Graph]\n"
                "Status: Knowledge Graph traversal unavailable or no linked graph relationship nodes."
            )

        # ── Pinecone Vector Search Source ──────────────────────────────────
        if vector_items:
            # Cap each vector chunk content to 500 chars to avoid overwhelming structured risk metrics
            vector_lines = []
            for item in vector_items:
                raw_content = str(item.get("content", ""))[:500]
                vector_lines.append(f"- {raw_content}")
            context_blocks.append(
                f"### [SOURCE: Pinecone Vector Search]\n" + "\n".join(vector_lines)
            )
        else:
            context_blocks.append(
                "### [SOURCE: Pinecone Vector Search]\n"
                "Status: Vector document passage retrieval unavailable or no matching agreement chunks."
            )

        # ── Limitation Notices ─────────────────────────────────────────────
        has_vector = statuses.get("vector", False)
        has_graph = statuses.get("graph", False)

        if not has_vector and not has_graph:
            context_blocks.append(
                "[LIMITATION NOTICE: Operating in SQL-Only Mode. Pinecone vector document search and Neo4j Knowledge Graph traversal are currently unavailable.]"
            )
        elif not has_vector:
            context_blocks.append(
                "[LIMITATION NOTICE: Operating in Hybrid SQL + Graph Mode. Pinecone vector document search is currently unavailable.]"
            )
        elif not has_graph:
            context_blocks.append(
                "[LIMITATION NOTICE: Operating in Hybrid SQL + Vector Mode. Neo4j Knowledge Graph traversal is currently unavailable.]"
            )

        combined_context = "\n\n".join(context_blocks)

        prompt = f"""
### RETRIEVED HYBRID EVIDENCE CONTEXT:
{combined_context}

### USER QUESTION:
{user_query}

Synthesize a professional, accurate response based strictly on the retrieved evidence context above.
Cite exact source tags ([PostgreSQL], [Neo4j], [Pinecone]) for facts. If evidence is missing or marked as unavailable for an aspect, state "Insufficient data to determine this" for that aspect.
"""

        try:
            response = await self._llm.generate(prompt=prompt, system_prompt=COPILOT_SYSTEM_PROMPT)
        except Exception as exc:
            logger.error("copilot_agent.llm_generation_error", error=str(exc))
            response = "I encountered an error synthesizing the response from the intelligence engine. Please try again."

        return {
            "query": user_query,
            "response": response,
            "citations": context_blocks,
            "hybrid_retrieval_status": statuses,
            "evidence_sources": {
                "sql_count": len(sql_items),
                "graph_count": len(graph_items),
                "vector_count": len(vector_items),
            }
        }
