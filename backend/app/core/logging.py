"""
Structured Logging utility using structlog.
Configures JSON output for easy production log parsing.
"""
import logging
import sys
import structlog
from app.core.config import settings


def configure_logging() -> None:
    """Configures structured JSON logging for FastAPI and integrations."""
    
    # Map text levels to log module levels
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Format output as JSON in production/docker; pretty print in development
            structlog.processors.JSONRenderer() if settings.APP_ENV != "local" else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
