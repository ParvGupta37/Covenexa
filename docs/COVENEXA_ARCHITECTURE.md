# Covenexa — System Architecture Map

> **Version**: Post-Sprint 4 Audit | **Date**: August 2026

---

## 1. Repository Root Layout

```
Covenexa/
├── backend/           # FastAPI Python backend (DDD architecture)
├── frontend/          # React + TypeScript + Vite + TailwindCSS
├── ai/                # AI agents, engines, workflows, RAG, LLM
├── integrations/      # External clients (Postgres, Redis, Cohere, Pinecone, Neo4j, SEC)
├── event_bus/         # Redis Pub/Sub event infrastructure
├── knowledge-graph/   # Neo4j (currently stub)
├── rag-engine/        # RAG stub
├── compliance-engine/ # Compliance stub
├── financial-engine/  # Financial engine stub
├── orchestration/     # Orchestration stubs
├── uploads/           # Local file storage
└── docker-compose.yml
```

---

## 2. Frontend Architecture

### Stack
- React 18 + TypeScript + Vite + TailwindCSS + Zustand + Recharts + Axios

### Route Map

| Path | Page |
|------|------|
| `/login` | LoginPage |
| `/register` | RegisterPage |
| `/` | DashboardPage |
| `/risk` | RiskPage |
| `/copilot` | CopilotPage |
| `/stress` | StressTestPage |
| `/graph` | GraphPage |
| `/audit` | AuditPage |
| `/borrowers` | BorrowersPage |
| `/loans` | LoansPage |
| `/uploads` | UploadsPage |
| `/documents/:agreementId` | DocumentDetailPage |

### Global State (Zustand)

- **auth.store**: `{ user, isLoading, setUser, logout }`
- **company.store**: `{ companies[], selectedCompanyId, selectedCompany, fetchCompanies(), registerCompany() }` — persisted to `localStorage["selected_company_id"]`

---

## 3. Backend Architecture (DDD)

### API Endpoints under `/api/v1`

| Endpoint | File |
|----------|------|
| `/auth/login`, `/auth/me` | auth.py |
| `/organizations` | organizations.py |
| `/borrowers` | borrowers.py |
| `/loans` | loans.py |
| `/uploads/`, `/uploads/sec-url` | uploads.py |
| `/documents/loan/:id`, `/borrower/:id`, `/:id/chunks|covenants|financials` | documents.py |
| `/risk/health/:id`, `/risk/default/:id`, `/risk/covenants/:id`, `/risk/stress`, `/risk/recommendations/:id`, `/risk/graph/:id`, `/risk/pipeline/:id` | risk.py |
| `/alerts/` | alerts.py |
| `/copilot/query` | copilot.py |
| `/audit/` | audit.py |
| `/reports/credit-memo` | reports.py |

---

## 4. Database — 19 Tables

### Migration Chain
```
0001 → organizations, users, borrowers, loans, agreements, financial_statements, compliance_results, reports
0002 → document_chunks, covenants, financial_metrics (+ agreement pipeline columns)
0003 → borrower_health_scores, risk_assessments, covenant_monitoring, alerts, stress_test_results, ai_recommendations
0004 → audit_logs
```

### Entity Hierarchy
```
organizations
  └── borrowers
        └── loans
              └── agreements
                    ├── document_chunks
                    ├── covenants          (also → borrowers)
                    └── financial_metrics  (also → borrowers)

borrowers → borrower_health_scores, risk_assessments, covenant_monitoring,
            alerts, stress_test_results, ai_recommendations, reports
```

### Source of Truth

| Concept | Canonical Table | Notes |
|---------|----------------|-------|
| Organization | `organizations` | |
| Borrower | `borrowers` | |
| Loan Facility | `loans` | |
| Agreement/Document | `agreements` | |
| Covenant definitions | `covenants` | AI-extracted |
| Financial data | `financial_metrics` | `financial_statements` is legacy Sprint 1 |
| Document chunks | `document_chunks` | |
| Health score | `borrower_health_scores` | Latest row = current; accumulates |
| Default probability | `risk_assessments` | Latest row = current; accumulates |
| Covenant compliance | `covenant_monitoring` | Replaced each pipeline run |
| AI recommendations | `ai_recommendations` | **Accumulates without cleanup** |
| Alerts | `alerts` | Appended, never pruned |
| Stress tests | `stress_test_results` | Appended per run |
| Audit events | `audit_logs` | |

---

## 5. Document Ingestion Flow

### File Upload
```
UploadsPage → POST /uploads/ (multipart: loan_id, file)
  → UploadDocumentHandler → saves file → creates agreements row → publishes Redis event
  → Redis EventBus → DocumentUploadedHandler → DocumentWorkflow (LangGraph)
```

### SEC EDGAR
```
UploadsPage → POST /uploads/sec-url { loan_id, sec_url }
  → SECDocumentPipeline → downloads HTML → creates agreements row → runs DocumentWorkflow (synchronous)
```

### AI Document Workflow (LangGraph)
```
START → DocumentAgent (parse + chunk + embed → Pinecone + document_chunks)
      → CovenantAgent (LLM extraction → covenants table)
      → FinancialAgent (LLM extraction → financial_metrics table)
      → Auto-triggers RiskIntelligencePipeline
END
```

---

## 6. Risk Intelligence Pipeline

```
RiskIntelligencePipeline.run_full_pipeline(session, borrower_id)
  1. FinancialEngine       → computes ratios → updates financial_metrics
  2. CovenantMonitor       → DELETE + INSERT covenant_monitoring (per covenant)
  3. HealthScoreEngine     → INSERT borrower_health_scores (accumulates)
  4. DefaultPredictor      → INSERT risk_assessments (accumulates)
  5. RecommendationEngine  → INSERT ai_recommendations (accumulates — NO cleanup)
  6. AlertEngine           → INSERT alerts if threshold breached
```

**Triggers:**
- Auto: after document workflow completes
- Auto: GET /risk/health if no score but metrics exist
- Auto: GET /risk/recommendations if no recommendations exist
- Manual: POST /risk/pipeline/:borrower_id

---

## 7. AI Copilot Flow

```
CopilotPage → POST /copilot/query { query, borrower_id }
  → CopilotAgent.run()
      1. SQL context: borrower profile + health score + covenants + financial_metrics
      2. LLM synthesis via Cohere Command A (mock if no API key)
      3. Returns { response, citations }

NOTE: Pinecone (vector) and Neo4j (graph) retrieval are NOT wired into CopilotAgent.
Only SQL context is used.
```

---

## 8. Knowledge Graph Flow

```
GET /risk/graph/{borrower_id}
  → Builds graph in-memory from PostgreSQL (NOT Neo4j)
  → Nodes: borrower, loans, agreements, covenants, financial_metrics
  → Returns { nodes[], edges[] } to GraphPage

NOTE: Neo4j is connected on startup but not queried anywhere in the active codebase.
```

---

## 9. Stress Testing Flow

```
StressTestPage → POST /risk/stress { borrower_id, revenue_change_pct, ebitda_change_pct, ... }
  → StressTester.run_scenario()
      → Fetches latest financial_metrics
      → Applies stress deltas to rev/ebitda/debt/interest
      → Evaluates covenants under stress (by name keyword match)
      → Calculates projected health: 75 - (breaches*20) - (leverage*5) + (coverage*3)
      → Calculates projected default: (100 - health) * 0.8
      → INSERT stress_test_results
      → Returns result
```

---

## 10. Authentication Flow

```
POST /auth/login → JWT access_token
Frontend: token stored in localStorage, attached to all Axios requests
GET /auth/me → restore session on page load
ProtectedRoute: redirects to /login if user is null
```

---

## 11. Event Bus

```
Redis Pub/Sub channel: "DocumentUploadedEvent"
Publisher: UploadDocumentHandler (file uploads only)
Consumer: DocumentUploadedHandler → DocumentWorkflow
SEC URL ingestion: bypasses event bus, runs synchronously
```

---

## 12. External Services

| Service | Status |
|---------|--------|
| PostgreSQL | Active |
| Redis | Active (event bus) |
| Cohere Command A + Embed v4 | Active (mock fallback if no key) |
| Pinecone (covenexa-docs index) | Active (stores document chunks) |
| Neo4j | Connected but not queried |
| SEC EDGAR | Active |

---

## 13. Module Dependencies

```
frontend/pages → company.store → api.ts → backend

backend/api → application/handlers → infrastructure/repositories → PostgreSQL
           → ai/engines (direct import in risk.py)
           → ai/workflows (via Redis event bus)
           → integrations/sec (direct import in uploads.py)

ai/workflows → ai/agents → ai/llm → integrations/cohere
            → integrations/postgres (for auto-trigger session)
            → integrations/pinecone (for chunk embedding)

ai/engines → SQLAlchemy session (raw SQL via text())
```
