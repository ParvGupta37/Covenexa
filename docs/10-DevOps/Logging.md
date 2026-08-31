# Logging

## Backend Logging

Covenexa uses **structlog** for structured JSON logging throughout the backend.

### Configuration

```python
# app/core/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
```

### Log Format

```json
{
  "timestamp": "2025-12-01T10:30:00Z",
  "level": "info",
  "event": "document_pipeline_started",
  "agreement_id": "uuid",
  "borrower_id": "uuid"
}
```

### Key Log Events

| Event | Level | When |
|:------|:------|:-----|
| `document_pipeline_started` | info | DocumentWorkflow begins |
| `document_pipeline_completed` | info | All agents finish |
| `document_pipeline_failed` | error | Any agent error |
| `risk_pipeline_completed` | info | Risk pipeline done |
| `cohere_api_mock_mode` | warning | No API key — using mock |
| `pinecone_upsert_success` | info | Chunk embedded and stored |
| `covenant_extraction_complete` | info | N covenants extracted |
| `user_login` | info | Successful authentication |

### Local Log Viewing

```bash
# Backend logs follow stdout — view with:
uvicorn app.main:app --port 8000 --reload 2>&1 | head -50

# Or with Docker Compose:
docker-compose logs -f covenexa_backend
```

## Frontend Logging

No structured logging in v1.0 frontend. Browser console logs are used in development.

For production, integrate a client-side error tracking service (e.g., Sentry) to capture JavaScript exceptions.
