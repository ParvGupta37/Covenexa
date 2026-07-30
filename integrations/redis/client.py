"""
Redis async client.
This is the ONLY place in the codebase that imports the redis-py library.

Three logical Redis databases are used:
  DB 0 — General cache (session data, computed results)
  DB 1 — Event Bus (Pub/Sub channels)
  DB 2 — Agent Shared Memory
"""
import json
import logging
from typing import Any

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Async Redis client supporting cache operations, pub/sub, and TTL management.

    Usage:
        client = RedisClient(url="redis://:password@redis:6379/0")
        await client.initialize()
        await client.set("key", {"data": "value"}, ttl=300)
        value = await client.get("key")
    """

    def __init__(self, url: str, decode_responses: bool = True) -> None:
        self._url = url
        self._decode_responses = decode_responses
        self._client: Redis | None = None

    async def initialize(self) -> None:
        """Create the async Redis connection pool."""
        if self._client is not None:
            logger.warning("RedisClient already initialized.")
            return

        logger.info("Initializing Redis client...")
        self._client = aioredis.from_url(
            self._url,
            decode_responses=self._decode_responses,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30,
        )
        # Verify connection immediately
        await self._client.ping()
        logger.info("Redis client initialized and connected.")

    def _ensure_initialized(self) -> Redis:
        if self._client is None:
            raise RuntimeError("RedisClient is not initialized. Call initialize() first.")
        return self._client

    # ── CACHE OPERATIONS ─────────────────────────────────────────

    async def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """
        Store a value in Redis.
        Value is JSON-serialized if it is not a string.
        """
        client = self._ensure_initialized()
        serialized = value if isinstance(value, str) else json.dumps(value)
        if ttl:
            await client.setex(key, ttl, serialized)
        else:
            await client.set(key, serialized)

    async def get(self, key: str) -> Any | None:
        """
        Retrieve a value from Redis.
        Attempts JSON deserialization; falls back to raw string.
        """
        client = self._ensure_initialized()
        raw = await client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys. Returns count of deleted keys."""
        client = self._ensure_initialized()
        return await client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if a key exists."""
        client = self._ensure_initialized()
        return bool(await client.exists(key))

    async def expire(self, key: str, ttl: int) -> None:
        """Set expiry on an existing key."""
        client = self._ensure_initialized()
        await client.expire(key, ttl)

    async def keys(self, pattern: str = "*") -> list[str]:
        """Return all keys matching a pattern. Use with caution in production."""
        client = self._ensure_initialized()
        return await client.keys(pattern)

    # ── HASH OPERATIONS ──────────────────────────────────────────

    async def hset(self, name: str, mapping: dict[str, Any]) -> None:
        """Set multiple fields in a hash."""
        client = self._ensure_initialized()
        serialized = {k: json.dumps(v) if not isinstance(v, str) else v for k, v in mapping.items()}
        await client.hset(name, mapping=serialized)

    async def hget(self, name: str, key: str) -> Any | None:
        """Get a single field from a hash."""
        client = self._ensure_initialized()
        raw = await client.hget(name, key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def hgetall(self, name: str) -> dict[str, Any]:
        """Get all fields and values from a hash."""
        client = self._ensure_initialized()
        raw = await client.hgetall(name)
        result = {}
        for k, v in raw.items():
            try:
                result[k] = json.loads(v)
            except (json.JSONDecodeError, TypeError):
                result[k] = v
        return result

    # ── PUB/SUB ──────────────────────────────────────────────────

    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a Redis Pub/Sub channel.

        Returns:
            Number of subscribers that received the message.
        """
        client = self._ensure_initialized()
        payload = message if isinstance(message, str) else json.dumps(message)
        return await client.publish(channel, payload)

    async def subscribe(self, *channels: str) -> PubSub:
        """
        Subscribe to one or more channels.

        Returns:
            PubSub object for reading messages.
        """
        client = self._ensure_initialized()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        return pubsub

    # ── HEALTH ───────────────────────────────────────────────────

    async def ping(self) -> bool:
        """Return True if Redis is reachable."""
        try:
            client = self._ensure_initialized()
            return await client.ping()
        except Exception:
            return False

    async def close(self) -> None:
        """Close the Redis connection pool."""
        if self._client is not None:
            logger.info("Closing Redis client...")
            await self._client.aclose()
            self._client = None
            logger.info("Redis client closed.")
