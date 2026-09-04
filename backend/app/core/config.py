"""
Backend application configurations and environment variable parser using Pydantic Settings.
"""
import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],   # works from both backend/ and project root
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_NAME: str = "Covenexa"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "INFO"

    # Security
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_SECRET_KEY_FOR_SECURITY_REASONS"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://covenexa_user:covenexa_pass@localhost:5432/covenexa"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        if not v:
            return v
        # Normalize Railway or standard Postgres URL schemes to asyncpg
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "covenexa_neo4j_pass"
    NEO4J_DATABASE: str | None = None
    REDIS_URL: str = "redis://:covenexa_redis_pass@redis:6379/0"

    # MCP Server
    MCP_SERVER_URL: str = "http://mcp_server:8001"

    # CORS – stored as a raw string, parsed via property below.
    # Acceptable formats in .env:
    #   CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://covenexa.vercel.app
    #   CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","https://covenexa.vercel.app"]
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://covenexa.vercel.app"

    # File Storage
    UPLOAD_DIR: str = "uploads"
    UPLOAD_MAX_SIZE_MB: int = 50
    ALLOWED_UPLOAD_EXTENSIONS: str = "pdf,docx,xlsx,csv,txt"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = "us-east-1"
    PINECONE_INDEX_NAME: str = "covenexa-docs"

    # Cohere
    COHERE_API_KEY: str = ""
    COHERE_LLM_MODEL: str = "command-a-03-2025"
    COHERE_EMBED_MODEL: str = "embed-english-v3.0"

    # Llama Parse / Cloud
    LLAMA_CLOUD_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into a list (supports JSON array or CSV)."""
        raw = self.CORS_ORIGINS.strip()
        origins: List[str] = []
        if raw.startswith("["):
            try:
                origins = [str(o).rstrip("/") for o in json.loads(raw) if o]
            except Exception:
                pass
        else:
            origins = [o.strip().rstrip("/") for o in raw.split(",") if o.strip()]

        # Ensure official production Vercel frontend is always permitted
        prod_vercel = "https://covenexa.vercel.app"
        if prod_vercel not in origins:
            origins.append(prod_vercel)

        return origins

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_UPLOAD_EXTENSIONS.split(",")]


settings = Settings()
