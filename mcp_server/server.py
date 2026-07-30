"""
Covenexa MCP Server — Entry Point.

The MCP Server is an HTTP API that exposes infrastructure tools
to AI agents. Agents call this server instead of accessing
PostgreSQL, Neo4j, Redis, Pinecone, or the file system directly.

Architecture:
    AI Agent → MCP Server (HTTP) → Tool → Infrastructure

This separation:
  - Enforces a single access boundary for all AI infrastructure I/O
  - Enables centralized audit logging of every agent operation
  - Allows tools to be added/updated without changing agents
  - Makes infrastructure swappable behind a stable API
"""
import logging
import os
from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from integrations.neo4j.client import Neo4jClient
from integrations.postgres.client import PostgresClient
from integrations.redis.client import RedisClient
from mcp_server.registry import ToolRegistry
from mcp_server.tools.file_storage_tool import FileStorageTool
from mcp_server.tools.neo4j_tool import Neo4jTool
from mcp_server.tools.pinecone_tool import PineconeTool
from mcp_server.tools.postgres_tool import PostgresTool
from mcp_server.tools.redis_tool import RedisTool

# ── STRUCTURED LOGGING ───────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)

# ── GLOBAL CLIENTS ───────────────────────────────────────────────────
postgres_client: PostgresClient | None = None
neo4j_client: Neo4jClient | None = None
redis_client: RedisClient | None = None
tool_registry: ToolRegistry = ToolRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize all infrastructure clients on startup,
    gracefully dispose on shutdown.
    """
    global postgres_client, neo4j_client, redis_client

    logger.info("mcp_server.startup", message="Initializing infrastructure clients...")

    # PostgreSQL
    postgres_client = PostgresClient(
        database_url=os.environ["DATABASE_URL"],
        pool_size=int(os.getenv("DATABASE_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "5")),
    )
    postgres_client.initialize()

    # Neo4j
    neo4j_client = Neo4jClient(
        uri=os.environ["NEO4J_URI"],
        user=os.getenv("NEO4J_USER", "neo4j"),
        password=os.environ["NEO4J_PASSWORD"],
    )
    neo4j_client.initialize()

    # Redis
    redis_client = RedisClient(url=os.environ["REDIS_URL"])
    await redis_client.initialize()

    # ── REGISTER TOOLS ───────────────────────────────────────────────
    # PostgresTool requires a session per request; initialized in the route handler.
    # Register a sentinel here so the registry knows the tool exists.
    async with postgres_client.session() as session:
        tool_registry.register(PostgresTool(session))

    # Pinecone
    pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
    pinecone_env = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
    pinecone_index = os.getenv("PINECONE_INDEX_NAME", "covenexa-docs")
    pinecone_client = PineconeClient(
        api_key=pinecone_api_key,
        environment=pinecone_env,
        index_name=pinecone_index,
    )
    pinecone_client.initialize()

    tool_registry.register(Neo4jTool(neo4j_client))
    tool_registry.register(RedisTool(redis_client))
    tool_registry.register(PineconeTool(pinecone_client))
    tool_registry.register(
        FileStorageTool(base_upload_dir=os.getenv("UPLOAD_DIR", "/app/uploads"))
    )

    logger.info(
        "mcp_server.startup",
        message="All tools registered.",
        tools=tool_registry.list_tools(),
    )

    yield  # ── Application running ──────────────────────────────────

    # Shutdown
    logger.info("mcp_server.shutdown", message="Disposing infrastructure clients...")
    if redis_client:
        await redis_client.close()
    if neo4j_client:
        await neo4j_client.dispose()
    if postgres_client:
        await postgres_client.dispose()
    logger.info("mcp_server.shutdown", message="Shutdown complete.")


# ── FASTAPI APP ──────────────────────────────────────────────────────
app = FastAPI(
    title="Covenexa MCP Server",
    description=(
        "Model Context Protocol Server — the single gateway between "
        "AI agents and all Covenexa infrastructure (PostgreSQL, Neo4j, "
        "Redis, Pinecone, File Storage)."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to internal network in production
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REQUEST / RESPONSE MODELS ────────────────────────────────────────

class ToolExecutionRequest(BaseModel):
    tool_name: str
    operation: str
    params: dict = {}


class ToolExecutionResponse(BaseModel):
    tool_name: str
    operation: str
    success: bool
    data: object
    error: str | None = None


# ── ROUTES ───────────────────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Health check endpoint.
    Returns status of all registered tools and infrastructure.
    """
    return {
        "status": "healthy",
        "service": "mcp_server",
        "version": "0.1.0",
        "registered_tools": [t["name"] for t in tool_registry.list_tools()],
    }


@app.get("/tools", tags=["Tools"])
async def list_tools() -> dict:
    """List all registered MCP tools and their descriptions."""
    return {
        "tools": tool_registry.list_tools(),
        "total": len(tool_registry),
    }


@app.post("/tools/execute", response_model=ToolExecutionResponse, tags=["Tools"])
async def execute_tool(request: ToolExecutionRequest) -> ToolExecutionResponse:
    """
    Execute an MCP tool.

    The calling agent provides:
      - tool_name: which tool to use
      - operation: which operation within the tool
      - params: operation-specific parameters

    All agent ↔ infrastructure communication flows through this endpoint.
    """
    logger.info(
        "mcp_server.tool_execute",
        tool=request.tool_name,
        operation=request.operation,
    )

    # PostgresTool needs a fresh session per request
    if request.tool_name == "postgres" and postgres_client:
        async with postgres_client.session() as session:
            tool = PostgresTool(session)
            result = await tool.execute(
                operation=request.operation,
                **request.params,
            )
    else:
        result = await tool_registry.execute(
            request.tool_name,
            operation=request.operation,
            **request.params,
        )

    return ToolExecutionResponse(
        tool_name=request.tool_name,
        operation=request.operation,
        success=result.get("success", False),
        data=result.get("data"),
        error=result.get("error"),
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("mcp_server.unhandled_error", error=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal MCP Server error.", "detail": str(exc)},
    )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=int(os.getenv("MCP_SERVER_PORT", "8001")),
        reload=False,
        log_level="info",
    )
