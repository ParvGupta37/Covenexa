"""
Redis MCP Tool.
Exposes cache, shared memory, and event publishing for AI agents.
"""
import logging
from typing import Any

from mcp_server.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class RedisTool(BaseTool):
    """
    MCP Tool: Redis cache, shared memory, and event bus access.

    Supported operations:
      - get_memory: Read a value from the shared memory store
      - set_memory: Write a value to shared memory (with optional TTL)
      - delete_memory: Remove a key from shared memory
      - publish_event: Publish an event to the Event Bus channel
      - get_hash: Read a hash map from Redis
      - set_hash: Write a hash map to Redis
    """

    def __init__(self, redis_client: Any) -> None:
        self._client = redis_client

    @property
    def name(self) -> str:
        return "redis"

    @property
    def description(self) -> str:
        return (
            "Read and write agent shared memory via Redis. "
            "Use 'get_memory'/'set_memory' for key-value state. "
            "Use 'publish_event' to emit events to the Event Bus. "
            "Use 'get_hash'/'set_hash' for structured state (e.g., workflow context)."
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        operation = kwargs.get("operation", "get_memory")

        try:
            if operation == "get_memory":
                return await self._get_memory(kwargs.get("key", ""))
            elif operation == "set_memory":
                return await self._set_memory(
                    kwargs.get("key", ""),
                    kwargs.get("value"),
                    kwargs.get("ttl"),
                )
            elif operation == "delete_memory":
                return await self._delete_memory(kwargs.get("key", ""))
            elif operation == "publish_event":
                return await self._publish_event(
                    kwargs.get("channel", ""),
                    kwargs.get("message", {}),
                )
            elif operation == "get_hash":
                return await self._get_hash(kwargs.get("name", ""))
            elif operation == "set_hash":
                return await self._set_hash(
                    kwargs.get("name", ""),
                    kwargs.get("mapping", {}),
                )
            else:
                return {"success": False, "data": None, "error": f"Unknown operation: {operation}"}
        except Exception as exc:
            logger.error("RedisTool error [op=%s]: %s", operation, exc)
            return {"success": False, "data": None, "error": str(exc)}

    async def _get_memory(self, key: str) -> dict[str, Any]:
        value = await self._client.get(key)
        return {"success": True, "data": value, "error": None}

    async def _set_memory(
        self,
        key: str,
        value: Any,
        ttl: int | None,
    ) -> dict[str, Any]:
        await self._client.set(key, value, ttl=ttl)
        return {"success": True, "data": {"key": key}, "error": None}

    async def _delete_memory(self, key: str) -> dict[str, Any]:
        count = await self._client.delete(key)
        return {"success": True, "data": {"deleted": count}, "error": None}

    async def _publish_event(
        self,
        channel: str,
        message: Any,
    ) -> dict[str, Any]:
        subscribers = await self._client.publish(channel, message)
        return {"success": True, "data": {"subscribers": subscribers}, "error": None}

    async def _get_hash(self, name: str) -> dict[str, Any]:
        data = await self._client.hgetall(name)
        return {"success": True, "data": data, "error": None}

    async def _set_hash(
        self,
        name: str,
        mapping: dict[str, Any],
    ) -> dict[str, Any]:
        await self._client.hset(name, mapping)
        return {"success": True, "data": {"name": name}, "error": None}
