"""
Pinecone MCP Tool.
Exposes vector search and upsert for AI agents via the MCP boundary.
"""
import logging
from typing import Any

from mcp_server.tools.base_tool import BaseTool
from integrations.pinecone.client import PineconeClient

logger = logging.getLogger(__name__)


class PineconeTool(BaseTool):
    """
    MCP Tool: Semantic vector search via Pinecone.

    Supported operations:
      - upsert_vectors: Store embeddings with metadata
      - query_vectors: Semantic similarity search
      - delete_vectors: Remove embeddings by id
    """

    def __init__(self, pinecone_client: PineconeClient | None = None) -> None:
        self._client = pinecone_client

    @property
    def name(self) -> str:
        return "pinecone"

    @property
    def description(self) -> str:
        return (
            "Perform semantic vector search and embedding storage via Pinecone. "
            "Use 'query_vectors' to retrieve semantically similar document chunks. "
            "Use 'upsert_vectors' to index new document embeddings."
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Route to upsert_vectors, query_vectors, delete_vectors."""
        operation = kwargs.get("operation", "query_vectors")

        if self._client is None:
            return {
                "success": False,
                "data": None,
                "error": "PineconeClient not initialized in PineconeTool.",
            }

        try:
            if operation == "upsert_vectors":
                vectors = kwargs.get("vectors", [])
                await self._client.upsert(vectors)
                return {"success": True, "data": "Upsert completed successfully.", "error": None}

            elif operation == "query_vectors":
                embedding = kwargs.get("embedding", [])
                top_k = kwargs.get("top_k", 10)
                filter_dict = kwargs.get("filter")
                results = await self._client.query(embedding=embedding, top_k=top_k, filter=filter_dict)
                return {"success": True, "data": results, "error": None}

            elif operation == "delete_vectors":
                ids = kwargs.get("ids", [])
                await self._client.delete(ids)
                return {"success": True, "data": "Deletion completed successfully.", "error": None}

            else:
                return {"success": False, "data": None, "error": f"Unknown operation: {operation}"}
        except Exception as exc:
            logger.error("PineconeTool error [op=%s]: %s", operation, exc)
            return {"success": False, "data": None, "error": str(exc)}
