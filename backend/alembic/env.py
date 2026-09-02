import asyncio
import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Add app to path so we can import ORM models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.infrastructure.orm.base import Base
# Import all ORM models to populate Base.metadata
from app.infrastructure.orm import *  # noqa

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
try:
    config = context.config
    if config is not None and config.config_file_name is not None:
        fileConfig(config.config_file_name)
except Exception:
    config = None

# target_metadata is for autogenerate support
target_metadata = Base.metadata


def get_db_url() -> str:
    """Return database connection URL from environment variables."""
    url = os.getenv("DATABASE_URL")
    if not url:
        if os.getenv("APP_ENV") == "production":
            raise RuntimeError("DATABASE_URL is not set in production environment.")
        return "postgresql+asyncpg://covenexa_user:covenexa_pass@localhost:5432/covenexa"

    # Normalize Railway / standard PostgreSQL URL schemes:
    # postgres://... -> postgresql+asyncpg://...
    # postgresql://... -> postgresql+asyncpg://...
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    return url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_db_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_db_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if config is not None:
    if context.is_offline_mode():
        run_migrations_offline()
    else:
        asyncio.run(run_migrations_online())
