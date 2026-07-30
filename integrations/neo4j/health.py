"""Neo4j health check utility."""
import logging

from integrations.neo4j.client import Neo4jClient

logger = logging.getLogger(__name__)


async def check_neo4j_health(client: Neo4jClient) -> dict[str, str | bool]:
    """
    Verify Neo4j server is reachable and accepting queries.

    Returns:
        dict with 'healthy' bool and optional 'error' message.
    """
    try:
        is_connected = await client.verify_connectivity()
        if is_connected:
            return {"healthy": True, "service": "neo4j"}
        return {"healthy": False, "service": "neo4j", "error": "Could not connect"}
    except Exception as exc:
        logger.error("Neo4j health check failed: %s", exc)
        return {"healthy": False, "service": "neo4j", "error": str(exc)}
