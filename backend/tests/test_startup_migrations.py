"""
Tests for programmatic startup Alembic migrations.
"""
import os
from unittest.mock import MagicMock, patch
import pytest

from app.core.migrations import _find_alembic_ini, run_startup_migrations
from app.core.config import settings


class TestStartupMigrations:

    def test_find_alembic_ini_locates_existing_file(self):
        ini_path = _find_alembic_ini()
        assert ini_path.is_file()
        assert ini_path.name == "alembic.ini"

    @pytest.mark.asyncio
    async def test_run_startup_migrations_calls_alembic_upgrade_head(self):
        with patch("app.core.migrations.command.upgrade") as mock_upgrade:
            await run_startup_migrations()
            mock_upgrade.assert_called_once()
            args, kwargs = mock_upgrade.call_args
            assert args[1] == "head"

    @pytest.mark.asyncio
    async def test_run_startup_migrations_raises_runtime_error_in_production(self):
        with patch("app.core.migrations.command.upgrade", side_effect=Exception("Connection refused")):
            with patch.object(settings, "APP_ENV", "production"):
                with pytest.raises(RuntimeError, match="Database migration failed during production startup"):
                    await run_startup_migrations()

    @pytest.mark.asyncio
    async def test_run_startup_migrations_re_raises_in_non_production(self):
        with patch("app.core.migrations.command.upgrade", side_effect=ValueError("Test migration error")):
            with patch.object(settings, "APP_ENV", "development"):
                with pytest.raises(ValueError, match="Test migration error"):
                    await run_startup_migrations()
