# Background Jobs & Workers

## Overview

Covenexa uses **Redis Pub/Sub** as its async task mechanism (not Celery/RQ). The document processing pipeline runs as a background subscriber that consumes events published when a document is uploaded.

> See [`Event Bus.md`](./Event%20Bus.md) for the full event bus architecture.

---

## Background Subscriber

The document event subscriber starts automatically when the FastAPI app starts:

```python
# app/main.py
@app.on_event("startup")
async def startup():
    asyncio.create_task(start_document_subscriber())
```

The subscriber runs as an `asyncio` task — no separate process needed.

---

## Background Task Duration

| Task | Estimated Duration |
|:-----|:------------------|
| DocumentAgent (parse + embed 50-page PDF) | 15–60 seconds |
| CovenantAgent (LLM extraction) | 5–20 seconds |
| FinancialAgent (LLM extraction) | 5–15 seconds |
| RiskIntelligencePipeline | 3–10 seconds |
| Full pipeline (end-to-end) | 30–120 seconds |

---

## Status Tracking

The `agreements.parsing_status` column tracks pipeline state:

| Status | Meaning |
|:-------|:--------|
| `pending` | Document uploaded, pipeline not yet started |
| `processing` | DocumentWorkflow running |
| `completed` | All agents finished successfully |
| `failed` | Pipeline error — check logs |

Frontend polls the document status on the Documents page to show progress.

---

## v1.1: Celery Migration (Planned)

For production scale (100+ concurrent uploads), the asyncio subscriber should be replaced with a Celery worker pool using Redis as the broker. This enables:
- Multiple parallel workers
- Task retry logic
- Dead-letter queuing
- Monitoring via Flower UI
