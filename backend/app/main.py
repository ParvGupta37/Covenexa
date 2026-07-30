"""
Covenexa FastAPI Backend Application.
Core entry point configures lifespan hook, middlewares, and routers.
"""
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
    
    # Start Redis Event Bus listener for DocumentUploadedEvent
    from integrations.redis.client import RedisClient
    from event_bus.redis_event_bus import RedisEventBus
    from event_bus.handlers.document_handler import DocumentUploadedHandler
    
    redis_client = RedisClient(url=settings.REDIS_URL)
    await redis_client.initialize()
    event_bus = RedisEventBus(redis_client)
    await event_bus.start()
    
    handler = DocumentUploadedHandler()
    await event_bus.subscribe("DocumentUploadedEvent", handler.handle)
    app.state.event_bus = event_bus
    app.state.redis_client = redis_client
    
    yield
    
    logger.info("app.shutdown")
    await event_bus.stop()
    await redis_client.close()


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
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)},
    )
