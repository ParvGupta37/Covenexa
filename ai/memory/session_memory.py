"""
Session Memory storing conversational histories for Copilot chat contexts.
"""
from typing import Any, List, Optional
from ai.memory.base import BaseMemory
from integrations.redis.client import RedisClient


class SessionMemory(BaseMemory):
    """
    Manages conversational history limits for a user chat session in Redis.
    """

    def __init__(self, redis_client: RedisClient, session_id: str) -> None:
        self._client = redis_client
        self._session_id = session_id

    def _get_key(self) -> str:
        return f"session:chat:{self._session_id}"

    async def set(self, key: str, value: Any, ttl: Optional[int] = 3600) -> None:
        """Stores a general key-value pair tied to this session."""
        db_key = f"session:{self._session_id}:{key}"
        await self._client.set(db_key, value, ttl=ttl)

    async def get(self, key: str) -> Optional[Any]:
        db_key = f"session:{self._session_id}:{key}"
        return await self._client.get(db_key)

    async def delete(self, key: str) -> bool:
        db_key = f"session:{self._session_id}:{key}"
        deleted = await self._client.delete(db_key)
        return deleted > 0

    async def add_chat_message(self, role: str, content: str) -> None:
        """Append user/assistant message to the session conversational history list."""
        key = self._get_key()
        history = await self._client.get(key) or []
        history.append({"role": role, "content": content})
        # Store back with 1-hour expiration
        await self._client.set(key, history, ttl=3600)

    async def get_chat_history(self) -> List[dict]:
        """Fetch full conversation context logs."""
        key = self._get_key()
        return await self._client.get(key) or []
