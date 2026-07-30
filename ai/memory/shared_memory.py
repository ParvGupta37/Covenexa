"""
Shared Memory layer for cross-agent collaboration backed by Redis.
"""
from typing import Any, Optional
from ai.memory.base import BaseMemory
from integrations.redis.client import RedisClient


class SharedMemory(BaseMemory):
    """
    Exposes key-value stores for agent outcomes sharing using Redis.
    Uses Redis DB 2 as configured in settings.
    """

    def __init__(self, redis_client: RedisClient) -> None:
        self._client = redis_client

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        await self._client.set(key, value, ttl=ttl)

    async def get(self, key: str) -> Optional[Any]:
        return await self._client.get(key)

    async def delete(self, key: str) -> bool:
        deleted = await self._client.delete(key)
        return deleted > 0
