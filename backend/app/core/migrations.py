"""
Alembic programmatic migration runner for startup initialization.
Ensures database schema is up-to-date (head) before requests are served.
"""
import asyncio
from pathlib import Path
import structlog
from alembic import command
from alembic.config import Config

from app.core.config import settings

logger = structlog.get_logger(__name__)


def _find_alembic_ini() -> Path:
    """Locate alembic.ini from possible deployment and development directories."""
    candidates = [
        Path("/app/backend/alembic.ini"),
        Path("/app/alembic.ini"),
        Path(__file__).resolve().parents[2] / "alembic.ini",
        Path(__file__).resolve().parents[3] / "backend" / "alembic.ini",
        Path("backend/alembic.ini").resolve(),
        Path("alembic.ini").resolve(),
    ]
    for p in candidates:
        if p.is_file():
            return p
    raise FileNotFoundError(f"Could not locate alembic.ini in candidate paths: {[str(c) for c in candidates]}")


def _run_alembic_upgrade_sync() -> None:
    """Synchronous Alembic upgrade execution (executed in worker thread via asyncio.to_thread)."""
    ini_path = _find_alembic_ini()
    script_loc = ini_path.parent / "alembic"

    logger.info("db.migration.start", alembic_ini=str(ini_path), script_location=str(script_loc))
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option("script_location", str(script_loc))
    command.upgrade(alembic_cfg, "head")
    logger.info("db.migration.complete", target="head")


async def run_startup_migrations() -> None:
    """
    Run Alembic database migrations programmatically during application startup.
    Runs in a worker thread via asyncio.to_thread to avoid blocking the event loop
    and to prevent collision with asyncio.run() in alembic/env.py.
    """
    try:
        await asyncio.to_thread(_run_alembic_upgrade_sync)
    except Exception as exc:
        logger.error("db.migration.failed", error=str(exc), exc_info=True)
        if settings.APP_ENV == "production":
            raise RuntimeError(f"Database migration failed during production startup: {exc}") from exc
        raise
