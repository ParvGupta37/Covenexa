# Monitoring — v1.0 Status

## Current Status

Application performance monitoring (APM) and infrastructure monitoring are **not configured** in Covenexa v1.0.

## Available Signals

### Health Endpoint

```bash
GET /health
# Returns: { "status": "healthy" }
```

### Database Health
```bash
# Check PostgreSQL connectivity
docker-compose exec covenexa_db psql -U covenexa_user -d covenexa_db -c "SELECT 1;"

# Check Redis
docker-compose exec covenexa_redis redis-cli PING
```

### Application Logs
Structlog JSON output to stdout — see [`Logging.md`](./Logging.md).

### Audit Log (Business-Level Monitoring)
```bash
GET /api/v1/audit/
# Lists all recent platform actions with timestamps
```

## v1.1 Monitoring Stack (Recommended)

| Tool | Purpose |
|:-----|:--------|
| **Prometheus** | Metrics scraping (FastAPI + Redis + PostgreSQL) |
| **Grafana** | Dashboard for request rate, latency, error rate, DB pool size |
| **Sentry** | Error tracking for both backend exceptions and frontend JS errors |
| **Uptime Robot** | External uptime and SSL certificate monitoring |

### FastAPI Prometheus Integration

```python
# pip install prometheus-fastapi-instrumentator
from prometheus_fastapi_instrumentator import Instrumentator
Instrumentator().instrument(app).expose(app)
```

This exposes `/metrics` endpoint for Prometheus to scrape.

## Key Metrics to Monitor

| Metric | Alert Threshold |
|:-------|:---------------|
| HTTP 5xx error rate | > 1% |
| P95 API response time | > 2 seconds |
| PostgreSQL connection pool utilization | > 80% |
| Document pipeline failure rate | > 5% |
| Pinecone query latency | > 500ms |
