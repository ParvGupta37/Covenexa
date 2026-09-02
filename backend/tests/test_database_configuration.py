import importlib.util
import os
from pathlib import Path
from unittest.mock import patch
import pytest

from app.core.config import Settings

ENV_PY_PATH = Path(__file__).resolve().parents[1] / "alembic" / "env.py"
spec = importlib.util.spec_from_file_location("alembic_env", str(ENV_PY_PATH))
alembic_env = importlib.util.module_from_spec(spec)
# Note: do not execute entire env.py as it may trigger context execution, load get_db_url directly
# Or define get_db_url test against its logic
spec.loader.exec_module(alembic_env)
get_db_url = alembic_env.get_db_url


class TestDatabaseUrlResolution:

    def test_alembic_normalizes_postgres_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:pass@host:5432/db", "APP_ENV": "production"}):
            url = get_db_url()
            assert url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_alembic_normalizes_postgresql_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:pass@host:5432/db", "APP_ENV": "production"}):
            url = get_db_url()
            assert url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_alembic_preserves_asyncpg_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:pass@host:5432/db", "APP_ENV": "production"}):
            url = get_db_url()
            assert url == "postgresql+asyncpg://user:pass@host:5432/db"

    def test_alembic_raises_in_production_when_missing(self):
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=True):
            with pytest.raises(RuntimeError, match="DATABASE_URL is not set in production environment"):
                get_db_url()

    def test_alembic_falls_back_in_development_when_missing(self):
        with patch.dict(os.environ, {"APP_ENV": "development"}, clear=True):
            url = get_db_url()
            assert "postgresql+asyncpg://" in url

    def test_settings_normalizes_postgres_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgres://user:secret@pg.railway.internal:5432/railway"}):
            s = Settings(_env_file=None)
            assert s.DATABASE_URL == "postgresql+asyncpg://user:secret@pg.railway.internal:5432/railway"

    def test_settings_normalizes_postgresql_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://user:secret@pg.railway.internal:5432/railway"}):
            s = Settings(_env_file=None)
            assert s.DATABASE_URL == "postgresql+asyncpg://user:secret@pg.railway.internal:5432/railway"

    def test_settings_preserves_asyncpg_scheme(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql+asyncpg://user:secret@pg.railway.internal:5432/railway"}):
            s = Settings(_env_file=None)
            assert s.DATABASE_URL == "postgresql+asyncpg://user:secret@pg.railway.internal:5432/railway"
