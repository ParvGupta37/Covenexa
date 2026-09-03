"""
Covenexa FastAPI Backend Application.
Core entry point configures lifespan hook, middlewares, and routers.
"""
import asyncio
from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import setup_middlewares

# ── LOGGING CONFIGURATION ───────────────────────────────────────────
configure_logging()
logger = structlog.get_logger(__name__)


# ── LIFESPAN HOOK ───────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and teardown triggers."""
    logger.info("app.startup", environment=settings.APP_ENV, version=settings.APP_VERSION)

    # 1. Run database migrations before serving any requests
    from app.core.migrations import run_startup_migrations
    try:
        await run_startup_migrations()
    except Exception as exc:
        logger.error("app.startup_migration_aborted", error=str(exc))
        raise

    # 2. Start Redis Event Bus listener for DocumentUploadedEvent
    from integrations.redis.client import RedisClient
    from event_bus.redis_event_bus import RedisEventBus
    from event_bus.handlers.document_handler import DocumentUploadedHandler

    redis_client = RedisClient(url=settings.REDIS_URL)
    event_bus = None
    try:
        await redis_client.initialize()
        event_bus = RedisEventBus(redis_client)
        await event_bus.start()

        handler = DocumentUploadedHandler()
        await event_bus.subscribe("DocumentUploadedEvent", handler.handle)
        logger.info("app.redis_event_bus_initialized")
    except Exception as exc:
        logger.warning("app.redis_init_failed", error=str(exc))

    app.state.event_bus = event_bus
    app.state.redis_client = redis_client

    # Initialize Neo4j driver once at startup (MEDIUM-3 lifecycle fix).
    # The driver object is created regardless of Neo4j availability;
    # actual connectivity errors surface at query time, not here.
    from integrations.neo4j.client import Neo4jClient
    neo4j_client = Neo4jClient(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
    )
    try:
        neo4j_client.initialize()
        logger.info("app.neo4j_driver_initialized")
        try:
            is_connected = await asyncio.wait_for(neo4j_client.verify_connectivity(), timeout=5.0)
            if is_connected:
                logger.info("app.neo4j_connectivity_verified")
            else:
                logger.warning("app.neo4j_connectivity_failed")
        except asyncio.TimeoutError:
            logger.warning("app.neo4j_connectivity_timeout", timeout_seconds=5)
        except Exception as exc:
            logger.warning("app.neo4j_connectivity_check_failed", error=str(exc))
    except Exception as exc:
        logger.warning("app.neo4j_driver_init_failed", error=str(exc))
    app.state.neo4j_client = neo4j_client

    yield

    logger.info("app.shutdown")
    if event_bus is not None:
        try:
            await event_bus.stop()
        except Exception as exc:
            logger.warning("app.redis_event_bus_stop_failed", error=str(exc))
    try:
        await redis_client.close()
    except Exception as exc:
        logger.warning("app.redis_close_failed", error=str(exc))

    # Dispose Neo4j driver cleanly on shutdown.
    try:
        await neo4j_client.dispose()
        logger.info("app.neo4j_driver_disposed")
    except Exception as exc:
        logger.warning("app.neo4j_driver_dispose_failed", error=str(exc))



# ── FASTAPI FACTORY ────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="Covenexa — AI-native Covenant Intelligence SaaS API Gateway.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach timing and CORS policies
setup_middlewares(app)

# Include core router endpoints
app.include_router(v1_router)


# ── HEALTH ENDPOINTS ────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def root_health():
    """System heartbeat check."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


# ── EXCEPTION HANDLING ──────────────────────────────────────────────
@app.exception_handler(Exception)
async def catch_unhandled_exceptions(request: Request, exc: Exception) -> JSONResponse:
    logger.error("app.unhandled_error", path=request.url.path, error=str(exc), exc_info=True)
    body = {"detail": "An internal server error occurred."}
    if settings.APP_ENV == "development":
        body["error"] = str(exc)
    return JSONResponse(
        status_code=500,
        content=body,
    )
