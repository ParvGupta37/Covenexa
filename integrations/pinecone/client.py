"""
Pinecone integration client — Sprint 2 implementation.
Stores and retrieves 1024-dimensional Cohere Embed v4 vectors.
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)

_DIMENSION = 1024
_METRIC = "cosine"


class PineconeClient:
    """
    Pinecone vector database client.
    Auto-creates the index if it does not exist.
    Gracefully skips operations when API key is absent.
    """

    def __init__(self, api_key: str, environment: str, index_name: str) -> None:
        self._api_key = api_key
        self._environment = environment
        self._index_name = index_name
        self._index: Any = None
        self._available = bool(api_key and api_key != "not_set")

    def initialize(self) -> None:
        """Connect to Pinecone and get (or create) the index."""
        if not self._available:
            logger.warning("PineconeClient: No API key — vector operations will be skipped.")
            return
        try:
            from pinecone import Pinecone, ServerlessSpec
            pc = Pinecone(api_key=self._api_key)

            existing = [idx.name for idx in pc.list_indexes()]
            if self._index_name not in existing:
                logger.info("PineconeClient: Creating index '%s'.", self._index_name)
                pc.create_index(
                    name=self._index_name,
                    dimension=_DIMENSION,
                    metric=_METRIC,
                    spec=ServerlessSpec(cloud="aws", region="us-east-1"),
                )

            self._index = pc.Index(self._index_name)
            logger.info("PineconeClient connected to index '%s'.", self._index_name)
        except Exception as exc:
            logger.error("PineconeClient.initialize failed: %s", exc)
            self._available = False

    async def upsert(self, vectors: list[dict[str, Any]]) -> None:
        """
        Upsert vectors into Pinecone.
        Each vector: {"id": str, "values": list[float], "metadata": dict}
        """
        if not self._available or self._index is None:
            logger.debug("Pinecone unavailable — skipping upsert of %d vectors.", len(vectors))
            return
        try:
            # Pinecone client is sync; run in thread
            import asyncio
            await asyncio.to_thread(self._index.upsert, vectors=vectors)
            logger.info("PineconeClient: upserted %d vectors.", len(vectors))
        except Exception as exc:
            logger.error("PineconeClient.upsert failed: %s", exc)

    async def query(
        self,
        embedding: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Query Pinecone for semantically similar vectors.
        Returns list of {id, score, metadata} dicts.
        """
        if not self._available or self._index is None:
            return []
        try:
            import asyncio
            kwargs: dict[str, Any] = {
                "vector": embedding,
                "top_k": top_k,
                "include_metadata": True,
            }
            if filter:
                kwargs["filter"] = filter
            result = await asyncio.to_thread(self._index.query, **kwargs)
            return [
                {"id": m.id, "score": m.score, "metadata": m.metadata or {}}
                for m in result.matches
            ]
        except Exception as exc:
            logger.error("PineconeClient.query failed: %s", exc)
            return []

    async def delete(self, ids: list[str]) -> None:
        """Delete vectors by ID."""
        if not self._available or self._index is None:
            return
        try:
            import asyncio
            await asyncio.to_thread(self._index.delete, ids=ids)
        except Exception as exc:
            logger.error("PineconeClient.delete failed: %s", exc)
