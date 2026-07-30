"""
Covenexa Integrations Package.
External service clients are exposed from this package.
Each sub-package wraps one external service.

NOTE: Sub-packages are intentionally NOT eagerly imported here to avoid
requiring all optional dependencies (neo4j, redis, cohere, etc.) to be
installed in environments that only need a subset (e.g. the FastAPI backend
only needs postgres). Import directly from the relevant sub-package instead:

    from integrations.postgres.client import PostgresClient
    from integrations.neo4j.client import Neo4jClient
    from integrations.redis.client import RedisClient
"""

__all__ = [
    "PostgresClient",
    "Neo4jClient",
    "RedisClient",
]
