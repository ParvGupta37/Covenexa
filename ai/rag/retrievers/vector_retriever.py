"""
Pinecone vector semantic retriever.
Generates query embeddings using Cohere and performs similarity search in Pinecone.
"""
from typing import Any, List
import structlog
from ai.rag.retrievers.base_retriever import BaseRetriever
from integrations.cohere.client import CohereClient
from integrations.pinecone.client import PineconeClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class VectorRetriever(BaseRetriever):
    """
    Retrieves semantically similar document chunks from Pinecone.
    """

    def __init__(self, pinecone_client: PineconeClient | None = None, cohere_client: CohereClient | None = None) -> None:
        self._pinecone = pinecone_client or PineconeClient(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT,
            index_name=settings.PINECONE_INDEX_NAME,
        )
        self._pinecone.initialize()

        self._cohere = cohere_client or CohereClient(api_key=settings.COHERE_API_KEY)
        self._cohere.initialize()

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("vector.retrieve", query=query, limit=limit)
        try:
            # 1. Embed query
            embeddings = await self._cohere.embed([query], input_type="search_query")
            if not embeddings:
                return []
            
            # 2. Query Pinecone
            matches = await self._pinecone.query(
                embedding=embeddings[0],
                top_k=limit,
                filter=kwargs.get("filter")
            )

            # 3. Format results
            results = []
            for match in matches:
                metadata = match.get("metadata", {})
                results.append({
                    "source": "vector_database",
                    "content": f"Page {metadata.get('page_number', '?')} (Section: {metadata.get('section', 'General')}): {metadata.get('text', 'Content missing')}" if "text" in metadata else f"Chunk ID: {match.get('id')}",
                    "score": match.get("score", 0.0),
                    "metadata": metadata,
                })
            return results
        except Exception as exc:
            logger.error("vector.retrieve_failed", error=str(exc))
            return []
