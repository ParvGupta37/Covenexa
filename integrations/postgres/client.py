"""
PostgreSQL async client using SQLAlchemy with asyncpg driver.
This is the ONLY place in the codebase that imports SQLAlchemy engine/session.
All other layers receive sessions via dependency injection.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


class PostgresClient:
    """
    Manages the async SQLAlchemy engine and session factory.

    Usage:
        client = PostgresClient(database_url="postgresql+asyncpg://...")
        async with client.session() as session:
            result = await session.execute(...)
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        echo: bool = False,
    ) -> None:
        self._database_url = database_url
        self._pool_size = pool_size
        self._max_overflow = max_overflow
        self._echo = echo
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def initialize(self) -> None:
        """Create the engine and session factory. Must be called before use."""
        if self._engine is not None:
            logger.warning("PostgresClient already initialized.")
            return

        logger.info("Initializing PostgreSQL connection pool...")
        self._engine = create_async_engine(
            self._database_url,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            echo=self._echo,
            pool_pre_ping=True,  # Verify connection liveness before use
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        logger.info("PostgreSQL connection pool initialized.")

    def initialize_for_testing(self, database_url: str) -> None:
        """
        Create engine with NullPool for test isolation.
        Tests must manage transactions manually.
        """
        self._engine = create_async_engine(
            database_url,
            poolclass=NullPool,
            echo=True,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Provides a transactional database session.
        Automatically commits on success, rolls back on exception.
        """
        if self._session_factory is None:
            raise RuntimeError("PostgresClient is not initialized. Call initialize() first.")

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        """Gracefully close all connections in the pool."""
        if self._engine is not None:
            logger.info("Disposing PostgreSQL connection pool...")
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("PostgreSQL connection pool disposed.")

    @property
    def engine(self) -> AsyncEngine:
        if self._engine is None:
            raise RuntimeError("PostgresClient is not initialized.")
        return self._engine
