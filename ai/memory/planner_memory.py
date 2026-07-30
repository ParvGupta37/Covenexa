"""
Planner Memory layer.
Stores active workflow execution step records, pending lists, and task maps.
"""
from typing import Any, Optional
from ai.memory.base import BaseMemory
from integrations.redis.client import RedisClient


class PlannerMemory(BaseMemory):
    """
    Manages workflow execution sequence logs in Redis.
    """

    def __init__(self, redis_client: RedisClient, workflow_id: str) -> None:
        self._client = redis_client
        self._workflow_id = workflow_id

    def _get_key(self, key: str) -> str:
        return f"planner:{self._workflow_id}:{key}"

    async def set(self, key: str, value: Any, ttl: Optional[int] = 1800) -> None:
        db_key = self._get_key(key)
        await self._client.set(db_key, value, ttl=ttl)

    async def get(self, key: str) -> Optional[Any]:
        db_key = self._get_key(key)
        return await self._client.get(db_key)

    async def delete(self, key: str) -> bool:
        db_key = self._get_key(key)
        deleted = await self._client.delete(db_key)
        return deleted > 0
