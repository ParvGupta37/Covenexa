"""PostgreSQL health check utility."""
import logging

from sqlalchemy import text

from integrations.postgres.client import PostgresClient

logger = logging.getLogger(__name__)


async def check_postgres_health(client: PostgresClient) -> dict[str, str | bool]:
    """
    Perform a lightweight health check against PostgreSQL.

    Returns:
        dict with 'healthy' bool and optional 'error' message.
    """
    try:
        async with client.session() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        return {"healthy": True, "service": "postgresql"}
    except Exception as exc:
        logger.error("PostgreSQL health check failed: %s", exc)
        return {"healthy": False, "service": "postgresql", "error": str(exc)}
