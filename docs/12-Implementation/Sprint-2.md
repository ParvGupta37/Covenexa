# Sprint 2 — Document Intelligence & AI Pipeline

## Sprint Goal

Build the complete document intelligence pipeline: file upload, SEC EDGAR ingestion, LLM-powered covenant and financial metric extraction, Pinecone vector storage, Redis event bus, and the LangGraph multi-agent document workflow.

**Exit Criteria:** User can upload a PDF loan agreement and see extracted covenants and financial metrics in the UI.

---

## Objectives Completed

- [x] File upload API (`POST /uploads/` — multipart PDF/DOCX)
- [x] SEC EDGAR URL ingestion (`POST /uploads/sec-url`)
- [x] Redis event bus (`event_bus/` module) with `DocumentUploadedEvent`
- [x] Async Redis subscriber — DocumentUploadedHandler
- [x] LangGraph DocumentWorkflow (stateful directed graph)
- [x] DocumentAgent — LlamaIndex parsing + chunk splitting + Cohere embedding → Pinecone
- [x] CovenantAgent — LLM extraction of covenants (name, metric, threshold, operator)
- [x] FinancialAgent — LLM extraction of financial figures (revenue, EBITDA, debt, cash, etc.)
- [x] PostgreSQL schema — Wave 2: document_chunks, covenants, financial_metrics + agreement pipeline columns
- [x] Alembic migration (`0002_document_intelligence.py`)
- [x] Pinecone index setup (`covenexa-docs`, 1024-dimension Cohere Embed v4)
- [x] Document Intelligence API endpoints (`/documents/`)
- [x] UploadsPage — drag-and-drop upload + status display
- [x] DocumentDetailPage — chunks, covenants, financial metrics tabs
- [x] Mock LLM fallback for development without API keys

---

## Key Sprint 2 Decisions

| Decision | Detail |
|:---------|:-------|
| LangGraph over LangChain LCEL | LangGraph's stateful graph model better fits the sequential multi-step document pipeline |
| Redis Pub/Sub over Celery | Simpler infrastructure; no separate worker process needed for v1.0 |
| SEC URL → synchronous | SEC documents are small enough that async is unnecessary; users want immediate feedback |
| Pinecone namespace-per-agreement | Enables agreement-level isolation without per-borrower index overhead |
| Chunking: 1000 tokens, 200 overlap | Balances context completeness with embedding precision |
| Mock fallback | Allows development and testing without paid API keys |