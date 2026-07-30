"""
MCP Client for Covenexa AI Agents.
Provides a single interface for agents to execute infrastructure tools.
Executes tools in-process for reliability and performance in local dev mode.
"""
from typing import Any
import structlog

from app.core.config import settings
from integrations.postgres.client import PostgresClient
from integrations.neo4j.client import Neo4jClient
from integrations.redis.client import RedisClient
from integrations.pinecone.client import PineconeClient
from mcp_server.tools.postgres_tool import PostgresTool
from mcp_server.tools.neo4j_tool import Neo4jTool
from mcp_server.tools.redis_tool import RedisTool
from mcp_server.tools.pinecone_tool import PineconeTool
from mcp_server.tools.file_storage_tool import FileStorageTool

logger = structlog.get_logger(__name__)



class MCPClient:
    """
    MCP Client that executes registered tools in-process,
    respecting the MCP tool executor boundaries.
    """

    def __init__(self) -> None:
        self._pg_client = PostgresClient(
            database_url=settings.DATABASE_URL,
            pool_size=5,
            max_overflow=2,
        )
        self._pg_client.initialize()

        self._neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )
        self._neo4j_client.initialize()

        self._redis_client = RedisClient(url=settings.REDIS_URL)
        # Redis client initialize is async, we will lazily initialize it on execute if needed.

        self._pinecone_client = PineconeClient(
            api_key=settings.PINECONE_API_KEY,
            environment=settings.PINECONE_ENVIRONMENT,
            index_name=settings.PINECONE_INDEX_NAME,
        )
        self._pinecone_client.initialize()

        self._file_tool = FileStorageTool(base_upload_dir=settings.UPLOAD_DIR)

    async def execute_tool(self, tool_name: str, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Execute an MCP tool.
        Separates agents from direct DB dependencies.
        """
        logger.info("mcp_client.execute", tool=tool_name, operation=operation)

        try:
            if tool_name == "postgres":
                async with self._pg_client.session() as session:
                    tool = PostgresTool(session)
                    return await tool.execute(operation=operation, **params)

            elif tool_name == "neo4j":
                tool = Neo4jTool(self._neo4j_client)
                return await tool.execute(operation=operation, **params)

            elif tool_name == "redis":
                if not self._redis_client._client:
                    await self._redis_client.initialize()
                tool = RedisTool(self._redis_client)
                return await tool.execute(operation=operation, **params)

            elif tool_name == "pinecone":
                tool = PineconeTool(self._pinecone_client)
                return await tool.execute(operation=operation, **params)

            elif tool_name == "file_storage":
                return await self._file_tool.execute(operation=operation, **params)

            else:
                return {
                    "success": False,
                    "data": None,
                    "error": f"Unknown tool: {tool_name}",
                }
        except Exception as exc:
            logger.error("mcp_client.execute_failed", tool=tool_name, operation=operation, error=str(exc))
            return {
                "success": False,
                "data": None,
                "error": str(exc),
            }

    async def close(self) -> None:
        """Dispose client connections."""
        await self._pg_client.dispose()
        await self._neo4j_client.dispose()
        await self._redis_client.close()
