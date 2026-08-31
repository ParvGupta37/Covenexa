# Product Requirements Document (PRD)

## Product Name
**Covenexa** — AI Operating System for Private Credit

## Version
v1.0 (Production Build)

---

## Problem Statement

Private credit funds and direct lenders manage dozens to hundreds of loan agreements, each containing complex financial covenants. Monitoring covenant compliance is done manually — analysts review spreadsheets, PDFs, and financial statements periodically. This process is slow, error-prone, and reactive. Breaches are often caught weeks after they occur.

---

## Objective

Build an AI-native SaaS platform that continuously monitors private credit portfolios, extracts covenants from legal agreements, evaluates borrower financial health, and provides proactive risk intelligence before problems escalate.

---

## Core Features (Implemented in v1.0)

### Document Intelligence
- Upload loan agreements (PDF, DOCX) via drag-and-drop
- Ingest SEC EDGAR filings by URL
- LLM-powered covenant extraction (CovenantAgent via Cohere Command A)
- LLM-powered financial metric extraction (FinancialAgent)
- Chunk-level vector embeddings stored in Pinecone

### Financial Intelligence
- Compute financial ratios: Debt/EBITDA, Interest Coverage, Current Ratio, Gross Margin
- Altman Z-Score for default probability
- Borrower Health Score (0–100 composite, 5 dimensions)
- Trend analysis across reporting periods

### Covenant Monitoring
- Compliance check: each covenant threshold vs. actual metrics
- Headroom calculation (how far from breach)
- Status classification: `compliant`, `watch`, `breach`, `critical`
- Real-time alerts when thresholds are crossed

### Portfolio Stress Testing
- Shock simulation: apply % changes to revenue, EBITDA, debt, interest
- Evaluate covenant compliance under simulated conditions
- Projected health score and default probability under stress

### AI Recommendations
- Prioritized action items per borrower
- Severity classification: CRITICAL, HIGH, MEDIUM, LOW
- Evidence-backed rationale from financial data

### AI Copilot
- Natural language queries about any borrower or portfolio
- Hybrid context: SQL (financial data) + Pinecone (document chunks) + Neo4j (graph relationships)
- Citations included in responses

### Automated Reporting
- 6-section Executive Credit Memorandum (PDF-quality markdown)
- Includes: Executive Summary, Financial Analysis, Covenant Status, Stress Scenarios, Recommendations, Risk Rating

### Dashboard & Monitoring
- Portfolio-wide KPI cards: Health, High Risk Count, Covenants at Risk, Watchlist
- Risk distribution donut chart (computed from real data)
- Portfolio exposure aggregation from active facilities
- Real-time alerts feed

### Organization Management
- Multi-organization support
- Borrower registration per organization
- Admin RBAC with full organization deletion

---

## Non-Functional Requirements

| Requirement | Implementation |
|:------------|:--------------|
| Security | JWT access + refresh tokens, bcrypt password hashing, RBAC middleware |
| Auditability | `audit_logs` table captures every major action |
| Explainability | Citations in every AI response, labeled tooltips in UI |
| Data Integrity | `None ≠ 0` enforced — unanalyzed fields show `N/A`, never fake zeroes |
| Scalability | Async FastAPI, connection pooling, Redis event bus, Pinecone cloud |
| Tenant Isolation | Pinecone namespace-per-agreement, borrower_id scope on all queries |

---

## User Roles

| Role | Permissions |
|:-----|:-----------|
| ADMIN | Full access — create/delete orgs, manage users, all data |
| ANALYST | Read + upload + query — no org deletion |

---

## Out of Scope for v1.0

- Multi-tenancy at infrastructure level (same DB, scoped by org)
- Real-time WebSocket alerts (polling only)
- Mobile application
- Automated financial statement ingestion via bank APIs