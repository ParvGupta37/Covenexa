"""Redis health check utility."""
import logging

from integrations.redis.client import RedisClient

logger = logging.getLogger(__name__)


async def check_redis_health(client: RedisClient) -> dict[str, str | bool]:
    """
    Perform a PING health check against Redis.

    Returns:
        dict with 'healthy' bool and optional 'error'.
    """
    try:
        is_alive = await client.ping()
        return {"healthy": is_alive, "service": "redis"}
    except Exception as exc:
        logger.error("Redis health check failed: %s", exc)
        return {"healthy": False, "service": "redis", "error": str(exc)}
