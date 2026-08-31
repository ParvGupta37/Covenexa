"""
AI Copilot Agent — Sprint 4 (Phase 2 MEDIUM-1: Hybrid GraphRAG).
Answers conversational credit risk questions using active Hybrid GraphRAG:
- Structured Credit Risk & Financial Metrics (PostgreSQL SQLRetriever)
- Semantic Document Passages (Pinecone VectorRetriever with Cohere Embed)
- Knowledge Graph Traversal (Neo4j GraphRetriever)
- Cohere Command A Synthesis with strict source citation & evidence grounding
- Clean separation between polished user-facing response and structured evidence citations
"""
from __future__ import annotations

import re
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


def _strip_internal_source_tags(text: str) -> str:
    """
    Strips internal database infrastructure tags and source markers from user-facing answers
    (e.g., [PostgreSQL], [Neo4j], [Pinecone], [SOURCE: ...], etc.) to ensure clean, polished output.
    """
    if not text:
        return ""
    # Remove bracketed source tags
    cleaned = re.sub(r"\[(?:PostgreSQL|Neo4j|Pinecone|SQL|Graph|Vector)\]", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[SOURCE:\s*[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[LIMITATION NOTICE:[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    # Clean up double spaces or orphan parentheses resulting from stripped tags
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    # Fix whitespace on line starts/ends
    lines = [line.strip() for line in cleaned.splitlines()]
    return "\n".join(lines).strip()


COPILOT_SYSTEM_PROMPT = (
    "You are Covenexa AI Copilot, an expert AI Credit Analyst and Risk Officer for Private Credit portfolios. "
    "Answer user questions accurately, concisely, professionally, and in clean markdown using ONLY the provided evidence context. "
    "Do not include internal retrieval-system names, database names, vector database names, graph database names, source tags (such as [PostgreSQL], [Neo4j], [Pinecone]), or technical pipeline details in the answer. "
    "Provenance and citations are handled separately by the platform's user interface evidence panel. "
    "If evidence is missing or marked as unavailable for an aspect, state 'Insufficient data to determine this' for that aspect without mentioning internal database infrastructure. "
    "NEVER claim to have retrieved information from a source marked as unavailable or missing."
)


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
        and synthesizes a grounded, polished response with explicit evidence sources.
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

        # 2. Build structured evidence context blocks (Preserved with full provenance for citations panel)
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

        prompt = f"""[EVIDENCE CONTEXT]
{combined_context}

[USER QUESTION]
{user_query}

Please provide a clear, formatted professional credit analysis answering the user question based strictly on the evidence above. Return only the polished natural-language answer intended for the end user without internal database tags or system labels.
"""

        response = ""
        try:
            response = await self._llm.generate(
                prompt=prompt,
                system_prompt=COPILOT_SYSTEM_PROMPT,
                temperature=0.3,
            )
        except Exception as exc:
            logger.error("copilot_agent.llm_generation_error", error=str(exc))

        # Guarantee non-empty grounded response
        if not response or len(response.strip()) < 10:
            logger.warning("copilot_agent.empty_llm_response_fallback", query=user_query, raw_response=response)
            response = self._synthesize_fallback(user_query, sql_items, graph_items, vector_items, statuses)
        else:
            response = _strip_internal_source_tags(response)

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

    def _synthesize_fallback(
        self,
        query: str,
        sql_items: List[dict],
        graph_items: List[dict],
        vector_items: List[dict],
        statuses: Dict[str, bool],
    ) -> str:
        """
        Deterministic, evidence-grounded fallback synthesizer when external LLM generation is unavailable.
        Extracts facts directly from structured PostgreSQL metrics, covenants, and vector passages
        without exposing internal database infrastructure tags.
        """
        sections: List[str] = []

        # Find borrower info
        borrower_name = "Borrower"
        for item in sql_items:
            if item.get("type") == "borrower_profile":
                meta = item.get("metadata", {})
                borrower_name = meta.get("company_name", "Borrower")
                break

        sections.append(f"**Credit Intelligence Summary for {borrower_name}**")

        # Covenants
        cov_items = [i for i in sql_items if i.get("type") == "covenant_monitoring"]
        if cov_items:
            breached = [c for c in cov_items if str(c.get("metadata", {}).get("status", "")).upper() in ("BREACH", "CRITICAL")]
            compliant = [c for c in cov_items if str(c.get("metadata", {}).get("status", "")).upper() == "COMPLIANT"]
            unknown = [c for c in cov_items if str(c.get("metadata", {}).get("status", "")).upper() == "UNKNOWN"]

            cov_summary = f"- **Total Covenants Monitored:** {len(cov_items)}\n"
            cov_summary += f"- **Breached:** {len(breached)}\n"
            cov_summary += f"- **Compliant:** {len(compliant)}\n"
            cov_summary += f"- **Pending / Unknown (Missing Ratios):** {len(unknown)}\n\n"
            cov_summary += "**Covenant Breakdown:**\n"
            for c in cov_items:
                meta = c.get("metadata", {})
                cov_summary += f"- **{meta.get('covenant_name')}**: Status `{meta.get('status', 'UNKNOWN').upper()}` (Threshold: {meta.get('threshold_value', 'N/A')})\n"
            sections.append(cov_summary.strip())
        elif any("covenant" in query.lower() for _ in [1]):
            sections.append("- **Covenants:** No covenant records found in structured records for this borrower.")

        # Financial Metrics
        fin_items = [i for i in sql_items if i.get("type") == "financial_metrics"]
        if fin_items:
            f_meta = fin_items[0].get("metadata", {})
            fin_summary = "**Financial Metrics:**\n"
            if f_meta.get("revenue") is not None:
                fin_summary += f"- **Revenue:** ${float(f_meta['revenue']):,.2f}\n"
            if f_meta.get("total_debt") is not None:
                fin_summary += f"- **Total Debt:** ${float(f_meta['total_debt']):,.2f}\n"
            if f_meta.get("cash") is not None:
                fin_summary += f"- **Cash:** ${float(f_meta['cash']):,.2f}\n"
            if f_meta.get("leverage_ratio") is not None:
                fin_summary += f"- **Leverage Ratio:** {f_meta['leverage_ratio']}x\n"
            sections.append(fin_summary.strip())

        # Health & Risk Assessment
        health_items = [i for i in sql_items if i.get("type") == "health_score"]
        if health_items:
            h_meta = health_items[0].get("metadata", {})
            sections.append(
                f"- **Overall Health Score:** {h_meta.get('score', 'N/A')}/100 ({str(h_meta.get('category', '')).upper()})"
            )

        if not sections:
            return (
                "**Credit Intelligence Notice**\n\n"
                "Insufficient structured data or document passages found to answer the query. "
                "Please verify that credit agreements and financial statements are ingested for this entity."
            )

        return "\n\n".join(sections)
