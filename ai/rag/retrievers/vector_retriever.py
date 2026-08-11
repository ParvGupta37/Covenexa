"""
Pinecone vector semantic retriever.
Generates query embeddings using Cohere Embed v3 and performs similarity search in Pinecone.
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
    Retrieves semantically similar agreement and document passages from Pinecone.
    """

    def __init__(self, pinecone_client: PineconeClient | None = None, cohere_client: CohereClient | None = None) -> None:
        self._pinecone = pinecone_client or PineconeClient(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT,
            index_name=settings.PINECONE_INDEX_NAME,
        )
        self._cohere = cohere_client or CohereClient(api_key=settings.COHERE_API_KEY)

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("vector.retrieve", query=query, limit=limit)
        borrower_id = kwargs.get("borrower_id")

        try:
            self._pinecone.initialize()
            self._cohere.initialize()

            # 1. Embed search query using Cohere
            embeddings = await self._cohere.embed([query], input_type="search_query")
            if not embeddings:
                return []

            # 2. Build metadata filter
            filter_dict = {}
            if borrower_id:
                filter_dict["borrower_id"] = borrower_id

            # 3. Query Pinecone (Strictly tenant-isolated when borrower_id is provided)
            matches = await self._pinecone.query(
                embedding=embeddings[0],
                top_k=limit,
                filter=filter_dict if filter_dict else None
            )

            # 4. Format results
            results = []
            for match in matches:
                metadata = match.get("metadata", {})
                score = match.get("score", 0.0)
                text_content = metadata.get("text") or metadata.get("content") or f"Document Chunk ID: {match.get('id')}"
                page_num = metadata.get("page_number") or metadata.get("page") or "?"
                section_name = metadata.get("section") or "General"

                results.append({
                    "source": "pinecone_vector",
                    "content": f"[Document Passage | Page {page_num}, Section '{section_name}']: {text_content}",
                    "score": round(score, 4),
                    "metadata": metadata,
                })
            return results
        except Exception as exc:
            logger.warning("vector.retrieve_failed", error=str(exc))
            return []
