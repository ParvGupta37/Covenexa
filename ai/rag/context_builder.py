"""
RAG Context Builder.
Merges and formats hybrid retrieval results into a clean LLM context string.
"""
from typing import Any, Dict, List
import structlog

logger = structlog.get_logger(__name__)

_MAX_CONTEXT_CHARS = 12_000


class ContextBuilder:
    """
    Converts ranked retrieval results into structured context for LLM prompts.
    Groups results by source, adds citations, and respects token budget.
    """

    def build(self, results: List[Dict[str, Any]], query: str) -> str:
        """
        Build a formatted context string from ranked retrieval results.

        Returns:
            Multi-section context string ready for injection into an LLM prompt.
        """
        if not results:
            return "No relevant context found in the knowledge base for this query."

        sections: Dict[str, List[str]] = {
            "Vector Search Matches": [],
            "Knowledge Graph Relations": [],
            "Structured Database Records": [],
        }

        for item in results:
            source = item.get("source", "unknown")
            content = item.get("content", "").strip()
            score = item.get("score", 0.0)
            citation = f"[Source: {source}, Relevance: {score:.2f}]"

            if source == "vector_database":
                sections["Vector Search Matches"].append(f"• {content}\n  {citation}")
            elif source == "knowledge_graph":
                sections["Knowledge Graph Relations"].append(f"• {content}\n  {citation}")
            else:
                sections["Structured Database Records"].append(f"• {content}\n  {citation}")

        parts = [f"## CONTEXT FOR QUERY: {query}\n"]
        for section_title, items in sections.items():
            if items:
                parts.append(f"### {section_title}")
                parts.extend(items)
                parts.append("")

        context = "\n".join(parts)

        # Enforce character budget
        if len(context) > _MAX_CONTEXT_CHARS:
            context = context[:_MAX_CONTEXT_CHARS] + "\n\n[Context truncated to fit token limit]"

        logger.info("context_builder.built", sections=list(sections.keys()), total_chars=len(context))
        return context

    def build_json(self, results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """
        Format results as Cohere-compatible documents list for RAG chat.
        Returns: [{"title": ..., "snippet": ...}, ...]
        """
        docs = []
        for item in results:
            docs.append({
                "title": f"[{item.get('source', 'unknown')}] Relevance: {item.get('score', 0):.2f}",
                "snippet": item.get("content", "")[:500],
            })
        return docs
