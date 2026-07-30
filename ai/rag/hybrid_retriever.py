"""
Hybrid GraphRAG Retriever.
Runs Vector, Graph, and SQL retrievers in parallel and merges results by score.
"""
import asyncio
from typing import Any, Dict, List
import structlog

from ai.rag.retrievers.vector_retriever import VectorRetriever
from ai.rag.retrievers.graph_retriever import GraphRetriever
from ai.rag.retrievers.sql_retriever import SqlRetriever

logger = structlog.get_logger(__name__)

# Source weights for final ranking
_WEIGHTS = {
    "vector_database": 1.0,
    "knowledge_graph": 0.9,
    "postgres_covenants": 0.85,
    "postgres_financials": 0.80,
}


class HybridRetriever:
    """
    Orchestrates parallel retrieval from Pinecone (vector), Neo4j (graph),
    and PostgreSQL (SQL), then merges and re-ranks results.
    """

    def __init__(self) -> None:
        self._vector = VectorRetriever()
        self._graph = GraphRetriever()
        self._sql = SqlRetriever()

    async def retrieve(
        self,
        query: str,
        limit: int = 10,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Run all three retrievers concurrently, merge, and rank.

        kwargs:
            borrower_id: Filter results for a specific borrower
            agreement_id: Filter results for a specific agreement
        """
        logger.info("hybrid.retrieve.start", query=query, limit=limit)

        # Parallel execution
        vector_task = self._vector.retrieve(query, limit=limit // 2 + 1, **kwargs)
        graph_task = self._graph.retrieve(query, limit=limit // 2, **kwargs)
        sql_task = self._sql.retrieve(query, limit=limit // 2, **kwargs)

        vector_results, graph_results, sql_results = await asyncio.gather(
            vector_task, graph_task, sql_task, return_exceptions=True
        )

        # Collect, skipping any retriever that raised an exception
        all_results: List[Dict[str, Any]] = []
        for results in [vector_results, graph_results, sql_results]:
            if isinstance(results, Exception):
                logger.warning("hybrid.retriever_failed", error=str(results))
                continue
            all_results.extend(results)

        # Re-rank by (score × source_weight)
        def rank_score(item: Dict[str, Any]) -> float:
            raw_score = float(item.get("score", 0.5))
            weight = _WEIGHTS.get(item.get("source", ""), 0.7)
            return raw_score * weight

        ranked = sorted(all_results, key=rank_score, reverse=True)
        top_results = ranked[:limit]

        logger.info(
            "hybrid.retrieve.complete",
            total_candidates=len(all_results),
            returned=len(top_results),
        )
        return top_results
