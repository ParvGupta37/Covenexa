"""
Middleware setups.
Handles CORS, request tracking IDs, and endpoints execution metrics.
"""
import time
import uuid
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = structlog.get_logger(__name__)


class RequestTimingMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware:
      - Attaches a unique request ID to execution contexts
      - Measures routing latency and outputs structured logs
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Inject correlation ids into logging variables context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.4f}s"
            
            logger.info(
                "http.request",
                status_code=response.status_code,
                duration=f"{process_time:.4f}s",
            )
            return response
        except Exception as exc:
            from fastapi.responses import JSONResponse
            process_time = time.perf_counter() - start_time
            logger.error(
                "http.request.failed",
                error=str(exc),
                duration=f"{process_time:.4f}s",
                exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "An internal server error occurred.", "error": str(exc)},
                headers={"X-Request-ID": request_id, "X-Process-Time": f"{process_time:.4f}s"},
            )


def setup_middlewares(app: FastAPI) -> None:
    """Register all middlewares on the FastAPI instance."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestTimingMiddleware)
