# Workers

> See [`Background Jobs.md`](./Background%20Jobs.md) for the full background processing architecture.

## Worker Architecture (v1.0)

Covenexa uses a single asyncio-based subscriber pattern — no separate worker processes.

```
FastAPI Process (uvicorn)
  ├── HTTP request handlers  (main thread / event loop)
  └── Document subscriber    (asyncio background task)
        → DocumentWorkflow on "DocumentUploadedEvent"
```

## Production Scaling

For high-throughput production, add uvicorn workers:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Each worker has its own Redis subscriber — multiple concurrent documents can be processed in parallel (up to N workers).
