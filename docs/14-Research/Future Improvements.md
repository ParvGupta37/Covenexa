# Future Improvements & Roadmap

> This document captures known limitations in v1.0 and planned improvements for future sprints.

---

## High Priority (v1.1)

### Neo4j — Activate for Real Graph Queries
**Current state:** Neo4j is connected on startup but not queried. The Knowledge Graph page (`/app/graph`) is built from PostgreSQL data served as nodes and edges.

**Target:** Wire Neo4j into the graph retriever, writing Borrower → Loan → Agreement → Covenant nodes on every pipeline run. Query Neo4j in the Copilot for relationship-based reasoning.

**Effort:** High — requires Neo4j migration job, write adapter, and graph retriever integration.

---

### Pinecone — Wire into CopilotAgent
**Current state:** Pinecone stores document chunk embeddings correctly. The Vector Retriever works. But CopilotAgent currently only uses SQL context (borrower profile + health + financials).

**Target:** Enable the full Hybrid GraphRAG in CopilotAgent — merge SQL + Pinecone + Neo4j context before every LLM call.

**Effort:** Medium — HybridRetriever exists; needs to be called from CopilotAgent.run().

---

### AI Recommendations — Cleanup on Re-run
**Current state:** `ai_recommendations` accumulates indefinitely — every pipeline run appends new rows without deleting old ones. The frontend shows the "latest batch" by creation time but old rows pollute the table.

**Target:** On each pipeline run, DELETE existing recommendations for the borrower before inserting new ones (same pattern as `covenant_monitoring`).

**Effort:** Low — one-line change in `RecommendationEngine`.

---

### WebSocket Real-Time Alerts
**Current state:** Alerts are polled (Dashboard fetches on mount).

**Target:** Push alerts via WebSocket when the AI pipeline generates new ones. Use `websockets` or FastAPI's `WebSocket` route.

**Effort:** Medium.

---

## Medium Priority (v1.2)

### Multi-Tenant Infrastructure
**Current state:** All organizations share one PostgreSQL instance, isolated by `organization_id` FK scope. Single Pinecone index scoped by `borrower_id` metadata filter.

**Target:** True tenant isolation with separate database schemas (PostgreSQL schema-per-tenant) and Pinecone index-per-organization.

---

### Document Version Management
**Current state:** Multiple agreement uploads for the same loan create multiple rows. There's no "current version" concept enforced.

**Target:** Implement versioned agreement management — mark superseded versions, run compliance only on the current version.

---

### Financial Statement PDF Parser (Tabular)
**Current state:** Financial metrics are extracted by LLM from raw text. Tabular data in PDFs (e.g. income statements with columns) is often mis-extracted.

**Target:** Add a specialized table extraction layer (e.g. `pdfplumber`, `camelot`) for structured financial tables before LLM extraction.

---

### Automated Covenant Headroom Alerts
**Current state:** Alerts fire when covenant status changes to `breach` or `critical`.

**Target:** Add "approaching breach" alert at a configurable headroom threshold (e.g. < 15% headroom → generate `watch` alert).

---

## Low Priority / Research (v2.0)

### LLM Provider Flexibility
- Add support for OpenAI GPT-4o and Anthropic Claude as alternative providers
- Abstract LLM calls behind a `LLMClient` interface for easy provider switching

### Mobile Application
- React Native investor-facing mobile app for portfolio monitoring and alert notifications

### Automated Financial Statement Ingestion
- Direct bank API integrations (Plaid, banking partner APIs) for real-time financial data

### Benchmark Covenant Extraction Accuracy
- Build an evaluation dataset of 50+ real loan agreements with ground-truth covenants
- Measure extraction precision/recall and improve prompts

### Persistent Agent Memory
- Enable LangGraph memory persistence (LangSmith tracing + checkpoint store)
- Allow CopilotAgent to remember conversation context across sessions

### Compliance Report Scheduling
- Automated monthly/quarterly compliance reports emailed to configured recipients
- Report history and download archive

---

## Known Limitations in v1.0

| Limitation | Notes |
|:-----------|:------|
| Neo4j not queried | Connected but all graph data served from PostgreSQL |
| Pinecone not in CopilotAgent | Vector retriever works but not integrated into Copilot |
| Recommendations accumulate | Old recs not purged on re-run |
| Alerts not pruned | Alert table grows indefinitely |
| No token refresh | Access token expires in 30min — user must re-login |
| No rate limiting | API endpoints have no rate limit |
| Single LLM provider | Only Cohere — no fallback to OpenAI or Anthropic |
