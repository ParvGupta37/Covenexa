# Event Bus — Redis Pub/Sub

## Overview

Covenexa uses **Redis Pub/Sub** as an asynchronous event bus to decouple the document upload API from the AI processing pipeline. This ensures that the upload API responds immediately to the user while heavy AI processing happens in the background.

---

## Architecture

```
HTTP Request
  POST /api/v1/uploads/
         │
         ▼
  UploadDocumentHandler
  → Save file to /uploads/ directory
  → INSERT agreements row (parsing_status = "pending")
  → PUBLISH "DocumentUploadedEvent" to Redis
  → Return 200 OK immediately
         │
         ▼ (async, background)
  Redis Channel: "covenexa:events"
         │
         ▼
  DocumentUploadedHandler (subscriber)
  → Deserialize event
  → Run DocumentWorkflow (LangGraph)
         │
         ├──► DocumentAgent   → chunks + embeddings → Pinecone
         ├──► CovenantAgent   → covenant extraction
         ├──► FinancialAgent  → financial metric extraction
         └──► RiskPipeline    → health score + compliance + alerts
```

---

## Event Structure

```python
# event_bus/events/document_uploaded.py

@dataclass
class DocumentUploadedEvent:
    event_type: str = "DocumentUploadedEvent"
    agreement_id: str = ""
    loan_id: str = ""
    borrower_id: str = ""
    file_path: str = ""
    timestamp: str = ""
```

---

## File Structure

```
event_bus/
├── __init__.py
├── base.py               # BaseEvent abstract class
├── redis_event_bus.py    # RedisEventBus — publish() and subscribe()
├── events/
│   ├── document_uploaded.py
│   └── ...
└── handlers/
    ├── document_uploaded_handler.py
    └── ...
```

---

## Key Implementation Details

| Detail | Value |
|:-------|:------|
| Redis channel | `covenexa:events` |
| Publisher | `UploadDocumentHandler` (file uploads only) |
| Consumer | `DocumentUploadedHandler` → `DocumentWorkflow` |
| SEC URL ingestion | Bypasses event bus — runs `DocumentWorkflow` **synchronously** |
| Connection | `REDIS_URL` from environment (`redis://:password@host:port/db`) |

---

## Why SEC URL Ingestion is Synchronous

When a user submits an SEC EDGAR URL via `POST /uploads/sec-url`, the system:
1. Downloads the HTML filing via `httpx`
2. Runs the full `DocumentWorkflow` synchronously
3. Returns the result in the API response

This is intentional — SEC filings are typically smaller HTML documents and users expect immediate feedback on whether ingestion succeeded.

---

## Event Bus Configuration

```python
# event_bus/redis_event_bus.py
class RedisEventBus:
    async def publish(self, event: BaseEvent):
        await self.redis.publish("covenexa:events", event.json())

    async def subscribe(self, handler: Callable):
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe("covenexa:events")
            async for message in pubsub.listen():
                await handler(message)
```
