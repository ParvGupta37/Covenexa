"""
Neo4j async client.
This is the ONLY place in the codebase that imports the Neo4j driver.
All knowledge graph queries must go through this client.
"""
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Manages the Neo4j async driver and provides session context managers.

    Usage:
        client = Neo4jClient(uri="bolt://neo4j:7687", user="neo4j", password="...")
        async with client.session() as session:
            result = await session.run("MATCH (n) RETURN n LIMIT 5")
    """

    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        max_connection_pool_size: int = 50,
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._max_pool = max_connection_pool_size
        self._driver: AsyncDriver | None = None

    def initialize(self) -> None:
        """Create the Neo4j driver. Must be called before use."""
        if self._driver is not None:
            logger.warning("Neo4jClient already initialized.")
            return

        logger.info("Initializing Neo4j driver (uri=%s)...", self._uri)
        self._driver = AsyncGraphDatabase.driver(
            self._uri,
            auth=(self._user, self._password),
            max_connection_pool_size=self._max_pool,
        )
        logger.info("Neo4j driver initialized.")

    @asynccontextmanager
    async def session(
        self,
        database: str = "neo4j",
    ) -> AsyncGenerator[AsyncSession, None]:
        """Provide a managed Neo4j async session."""
        if self._driver is None:
            raise RuntimeError("Neo4jClient is not initialized. Call initialize() first.")

        async with self._driver.session(database=database) as session:
            yield session

    async def execute_query(
        self,
        cypher: str,
        parameters: dict[str, Any] | None = None,
        database: str = "neo4j",
    ) -> list[dict[str, Any]]:
        """
        Execute a read/write Cypher query and return results as a list of dicts.

        Args:
            cypher: Cypher query string.
            parameters: Query parameters dict.
            database: Target database name.

        Returns:
            List of result records as dicts.
        """
        if self._driver is None:
            raise RuntimeError("Neo4jClient is not initialized.")

        async with self.session(database=database) as session:
            result = await session.run(cypher, parameters or {})
            records = await result.data()
            return records

    async def verify_connectivity(self) -> bool:
        """Verify the driver can reach the Neo4j server."""
        try:
            if self._driver is None:
                return False
            await self._driver.verify_connectivity()
            return True
        except Exception as exc:
            logger.error("Neo4j connectivity check failed: %s", exc)
            return False

    async def dispose(self) -> None:
        """Close the driver and all open connections."""
        if self._driver is not None:
            logger.info("Closing Neo4j driver...")
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j driver closed.")
