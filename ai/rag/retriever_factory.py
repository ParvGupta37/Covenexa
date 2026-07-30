"""
Retriever factory class.
"""
from typing import Any, List
from ai.rag.retrievers.base_retriever import BaseRetriever
from ai.rag.retrievers.vector_retriever import VectorRetriever
from ai.rag.retrievers.graph_retriever import GraphRetriever
from ai.rag.retrievers.sql_retriever import SqlRetriever
from integrations.postgres.client import PostgresClient
from integrations.neo4j.client import Neo4jClient


class RetrieverFactory:
    """
    Constructs concrete database query retrievers based on active connections.
    """

    def __init__(
        self,
        postgres_client: PostgresClient,
        neo4j_client: Neo4jClient,
        pinecone_client: Any,
    ) -> None:
        self._postgres = postgres_client
        self._neo4j = neo4j_client
        self._pinecone = pinecone_client

    def get_all_retrievers(self) -> List[BaseRetriever]:
        """Expose all three RAG sources."""
        return [
            SqlRetriever(self._postgres),
            GraphRetriever(self._neo4j),
            VectorRetriever(self._pinecone),
        ]
