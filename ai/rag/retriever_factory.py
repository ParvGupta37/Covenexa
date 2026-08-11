"""
Retriever Factory — Sprint 4 (Phase 2 MEDIUM-1).
Constructs and orchestrates Hybrid RAG retrievers (SQL, Vector, Graph).
"""
from typing import Any, List, Dict
import structlog

from ai.rag.retrievers.base_retriever import BaseRetriever
from ai.rag.retrievers.vector_retriever import VectorRetriever
from ai.rag.retrievers.graph_retriever import GraphRetriever
from ai.rag.retrievers.sql_retriever import SqlRetriever
from integrations.postgres.client import PostgresClient
from integrations.neo4j.client import Neo4jClient
from integrations.pinecone.client import PineconeClient

logger = structlog.get_logger(__name__)


class RetrieverFactory:
    """
    Constructs concrete database query retrievers and orchestrates Hybrid RAG search.

    MEDIUM-3 fix: retrievers are created once at __init__ time and reused across
    queries. This prevents a new Neo4j driver pool and Pinecone client from being
    opened on every Copilot request.
    """

    def __init__(
        self,
        postgres_client: PostgresClient | None = None,
        neo4j_client: Neo4jClient | None = None,
        pinecone_client: PineconeClient | None = None,
    ) -> None:
        self._postgres = postgres_client
        self._neo4j = neo4j_client
        self._pinecone = pinecone_client

        # Build retrievers once — reused for all subsequent calls.
        self._sql_retriever = SqlRetriever(self._postgres)
        self._graph_retriever = GraphRetriever(self._neo4j)
        self._vector_retriever = VectorRetriever(self._pinecone)

    def get_all_retrievers(self) -> List[BaseRetriever]:
        """Expose all three RAG sources."""
        return [self._sql_retriever, self._graph_retriever, self._vector_retriever]

    async def retrieve_hybrid(
        self,
        query: str,
        limit: int = 5,
        borrower_id: str | None = None,
        session: Any = None,
    ) -> Dict[str, Any]:
        """
        Executes unified Hybrid RAG retrieval across SQL, Vector, and Graph.
        Returns detailed results and status per store to enable graceful fallback.
        """
        logger.info("hybrid_retriever.start", query=query, borrower_id=borrower_id)

        # 1. SQL Structured Retrieval
        sql_results = []
        try:
            sql_results = await self._sql_retriever.retrieve(
                query, limit=limit, borrower_id=borrower_id, session=session
            )
        except Exception as exc:
            logger.warning("hybrid.sql_failed", error=str(exc))

        # 2. Graph Relationship Retrieval (Neo4j)
        graph_results = []
        try:
            graph_results = await self._graph_retriever.retrieve(
                query, limit=limit, borrower_id=borrower_id
            )
        except Exception as exc:
            logger.warning("hybrid.graph_failed", error=str(exc))

        # 3. Vector Semantic Retrieval (Pinecone)
        vector_results = []
        try:
            vector_results = await self._vector_retriever.retrieve(
                query, limit=limit, borrower_id=borrower_id
            )
        except Exception as exc:
            logger.warning("hybrid.vector_failed", error=str(exc))


        statuses = {
            "sql": len(sql_results) > 0,
            "graph": len(graph_results) > 0,
            "vector": len(vector_results) > 0,
        }

        logger.info(
            "hybrid_retriever.completed",
            sql_count=len(sql_results),
            graph_count=len(graph_results),
            vector_count=len(vector_results),
            statuses=statuses,
        )

        return {
            "query": query,
            "borrower_id": borrower_id,
            "sql_results": sql_results,
            "graph_results": graph_results,
            "vector_results": vector_results,
            "statuses": statuses,
        }
