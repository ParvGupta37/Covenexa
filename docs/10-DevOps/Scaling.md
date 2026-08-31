# Scaling

## v1.0 Architecture (Single Process)

```
1 uvicorn process
  → 1 asyncio event loop
  → HTTP request handlers
  → Redis Pub/Sub subscriber (background task)
  → Direct PostgreSQL connections (SQLAlchemy connection pool)
```

Supports: ~50–100 concurrent users, ~10 concurrent document uploads.

---

## Horizontal Scaling (v1.1)

### Backend Workers

```bash
# Multiple uvicorn workers (pre-fork model)
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
```

Each worker is a separate Python process with its own event loop and DB connection pool.

### Database Connection Pool

```python
# Per worker: up to 10 connections (configurable)
engine = create_async_engine(DATABASE_URL, pool_size=10, max_overflow=5)
```

4 workers × 10 connections = 40 max PostgreSQL connections.  
Ensure `max_connections` in PostgreSQL is set accordingly (default: 100).

### Load Balancer

Put an Nginx or AWS ALB in front of multiple uvicorn processes:

```nginx
upstream covenexa_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### Celery Workers (Document Processing)

For high-volume document ingestion, migrate from asyncio subscriber to Celery:

```
Document Upload → Publish to Redis (Celery broker) → Celery Worker Pool (N workers)
```

Each worker handles one document pipeline at a time. Scale by adding workers.

---

## Database Scaling

| Layer | Scaling Strategy |
|:------|:----------------|
| PostgreSQL | Read replicas for analytics queries; PgBouncer connection pooler |
| Pinecone | Managed serverless — auto-scales |
| Neo4j | Neo4j Aura (managed) or Neo4j cluster |
| Redis | Redis Cluster or AWS ElastiCache |
