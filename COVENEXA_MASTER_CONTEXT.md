# COVENEXA — MASTER CONTEXT & ENGINEERING HANDOFF

> **Authoritative Context & Handoff Document**
> **Target Audience**: AI Assistant / Senior Engineer continuing Covenexa development and production deployment.
> **Date**: September 2026

---

## 1. PROJECT IDENTITY

### Name & Description
- **Project**: **Covenexa**
- **Headline**: AI-Powered Covenant Monitoring & Credit Risk Intelligence Platform.
- **Form Factor**: High-polish, institutional-grade SaaS platform built as a venture-grade portfolio product (not a classroom CRUD app).

### Core Problem Solved
Institutional private credit funds, commercial banks, and direct lending teams manage complex, bespoke credit agreements. Covenants (e.g., Maximum Leverage Ratio, Minimum Interest Coverage, Liquidity floors) are traditionally audited manually from dense PDF compliance certificates, SEC 10-Q/10-K filings, and quarterly balance sheets. This causes compliance delays, human error in ratio calculations, and lagging default detection.

Covenexa automates the entire covenant lifecycle: ingesting credit agreements and quarterly financial certificates, extracting complex financial metrics and legal terms via AI/RAG, evaluating covenant compliance status in real-time, calculating a 5-dimension Health Score, simulating stressed economic scenarios, mapping credit exposure across a Knowledge Graph, and providing an interactive AI Credit Copilot for portfolio analysts.

### Primary Workflow
```
Organization Registration & Setup
       │
       ▼
Team Members & RBAC (Admin, Manager, Analyst)
       │
       ▼
Borrower Entity Management
       │
       ▼
Loan Facilities (Multi-currency, Facility Limits)
       │
       ▼
Credit Agreements & Financial Documents (Upload PDF/TXT or URL Ingestion)
       │
       ▼
AI Extraction Engine (Financial Line Items + Covenant Ratio Thresholds)
       │
       ▼
Authoritative SQL Storage + Pinecone Vector Indexing + Neo4j Graph Ingestion
       │
       ▼
Covenant Monitoring Engine (Automated Ratio Calculation & Headroom Evaluation)
       │
       ▼
Risk Monitor Dashboard (Health Score, Default Probability, Prudential Risk Factors)
       │
       ▼
Stress Testing Engine (Macroeconomic shocks & 3-state facility resilience)
       │
       ▼
Knowledge Graph Explorer (Interactive borrower-loan-covenant-metric visual topology)
       │
       ▼
AI Credit Copilot (Institutional RAG assistant with account-isolated history & structured sources)
```

---

## 2. CURRENT TECHNOLOGY STACK

### Backend
- **Framework**: Python 3.11+ / 3.12, FastAPI (async execution)
- **ORM & Database Client**: SQLAlchemy 2.0 (Declarative Async), `asyncpg` driver
- **Schema Migrations**: Alembic (10 fully applied migration revisions)
- **Relational DB**: PostgreSQL 15/16/17 (Strictly native PostgreSQL; **NOT Supabase**)
- **Event Bus & Caching**: Redis 7 (Async `redis-py` / `aioredis` pub/sub and state cache)
- **Knowledge Graph**: Neo4j 5.x Community/Enterprise (Official `neo4j` async driver)
- **Vector Database**: Pinecone Serverless (1024-dim vectors, cosine distance)
- **AI / LLM Provider**: Cohere Command (`command-a-03-2025`) & Cohere Embed (`embed-english-v3.0`)
- **Document Parsing**: `pypdf`, BeautifulSoup4, `llamaparse` fallback client
- **Security & Auth**: PyJWT, `passlib` with bcrypt, HTTP Bearer tokens
- **Logging & Metrics**: `structlog` (structured JSON logging), request timing middleware with `X-Request-ID` tracing

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tooling & Dev Server**: Vite 5
- **Routing**: React Router DOM v6 (with SPA fallback & replace-navigation guards)
- **Styling**: TailwindCSS, CSS Variables, Institutional Dark Theme
- **Data Visualization**: Recharts (Risk distribution charts, financial trends)
- **Iconography**: Lucide React (`Building2`, `BarChart3`, `FileText`, `Scale`, `Activity`, `BrainCircuit`, `DollarSign`, etc.)
- **State Management**: Zustand (Auth, Company, Portfolio stores)

### Infrastructure & DevOps
- **Containerization**: Multi-stage Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`, `mcp_server/Dockerfile`)
- **Local Orchestration**: Docker Compose (`postgres:16-alpine`, `redis:7-alpine`, `neo4j:5.20`, `backend`, `frontend`, `mcp_server`)
- **CI/CD**: GitHub Actions ([`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml), [`.github/workflows/cd.yml`](file:///.github/workflows/cd.yml))

---

## 3. PROJECT ARCHITECTURE & DATA FLOW

```
[ Web Browser Client ]
        │
        ▼ (HTTPS / REST)
[ FastAPI Backend Gateway ] ── (CORS, JWT RBAC, Request Tracing)
   │     │            │
   │     │            ├──────────────────────────┐
   │     ▼            ▼                          ▼
   │  [PostgreSQL]  [Redis 7]                [Neo4j 5]
   │  (Relational)  (Cache & Event Bus)      (Knowledge Graph)
   │  - Auth/Tenants - DB 0: Metric Cache    - Borrowers
   │  - Borrowers    - DB 1: PubSub Events   - Loans
   │  - Loans        - DB 2: Shared Memory   - Agreements
   │  - Financials                           - Covenants
   │  - Covenants                            - Financials
   │  - Audit Logs
   │
   ├───────────────────────────────┐
   ▼                               ▼
[Pinecone Vector DB]      [Cohere Command & Embed]
- 1024-dim Embeddings      - LLM Synthesis
- Document Chunks          - Extraction Verification
- Cosine Similarity        - Copilot Explanations
```

### Component Roles & Responsibilities

1. **FastAPI Backend (`/app/main.py`)**:
   - Single point of entry for all business logic, credit calculations, AI orchestration, and RBAC enforcement.
   - Manages lifespan events: initializes Redis Event Bus subscriber and Neo4j async connection pool on startup; disposes cleanly on shutdown.
   - Hosts system health heartbeat at `GET /health`.

2. **PostgreSQL**:
   - Primary authoritative data store for all transactional entities, users, organizations, borrower financials, calculated health scores, risk assessments, and account-specific Copilot conversation records.

3. **Redis 7**:
   - **DB 0**: Fast key-value cache for hot portfolio statistics and computed risk summaries.
   - **DB 1**: Real-time Pub/Sub Event Bus (`RedisEventBus`) distributing `DocumentUploadedEvent` to background extraction handlers.
   - **DB 2**: Agent state memory and cross-request scratchpad.

4. **Neo4j Knowledge Graph**:
   - Stores credit relationship graph: `(:Borrower)-[:HOLDS]->(:Loan)-[:GOVERNED_BY]->(:Agreement)-[:CONTAINS]->(:Covenant)` and `(:Borrower)-[:REPORTED]->(:Financial)`.
   - Node upsert uses idempotent Cypher `MERGE` logic; respects entity archival state.

5. **Pinecone Vector Database**:
   - Stores 1024-dimensional document chunk embeddings with strict `borrower_id` and `organization_id` metadata filtering for tenant-isolated vector search.

6. **Cohere API**:
   - LLM synthesis for covenant interpretation and Copilot chat.
   - If `COHERE_API_KEY` is not present, all endpoints gracefully degrade to deterministic SQL-backed mock responses without throwing unhandled exceptions.

7. **File Storage**:
   - Uploaded PDF/TXT loan agreements are written to `settings.UPLOAD_DIR` (`/app/uploads`).
   - Filenames are sanitized via `os.path.basename` to prevent path traversal attacks (`../../../etc/passwd`).
   - For single-server deployments, persistent Docker named volumes (`uploads_data:/app/uploads`) are required.

---

## 4. DATABASE & ALEMBIC MIGRATIONS

> [!IMPORTANT]
> **Covenexa does NOT use Supabase.**
> Authentication, relational tables, and storage are built natively with PostgreSQL 15+, SQLAlchemy 2.0 async, and Alembic.

### Schema Management
- Schema creation in production is managed **strictly via Alembic migrations**.
- `Base.metadata.create_all()` is **never** executed during app startup.
- **Migration Command**:
  ```bash
  cd backend && alembic upgrade head
  ```

### Active Alembic Revisions (`backend/alembic/versions/`):
1. `0001_initial_schema.py`: Organizations, Users, Borrowers, Loans, Agreements, Covenants, Financials.
2. `0002_add_document_chunks_and_embeddings.py`: Chunk storage for RAG pipeline.
3. `0003_add_health_scores_and_risk_assessments.py`: Health score dimensions, default probabilities, recommendations.
4. `0004_add_invitations_and_rbac.py`: Team invites, token expirations, role flags.
5. `0005_add_audit_logs.py`: Audit trails for credit compliance changes.
6. `0006_add_currency_to_loans_and_financials.py`: Multi-currency support (USD, EUR, GBP, INR, IDR, etc.).
7. `0007_add_processing_status_to_agreements.py`: Asynchronous document processing state machine (`pending`, `parsing`, `done`, `failed`).
8. `0008_add_archival_to_borrowers_and_loans.py`: Non-destructive soft deletion (`is_archived`, `archived_at`, `archived_by`).
9. `0009_fix_covenant_loan_relationship.py`: Re-parents covenant references cleanly through agreements.
10. `0010_add_copilot_conversations_and_messages.py`: Account-isolated chat history tables (`copilot_conversations`, `copilot_messages`).

---

## 5. AUTHENTICATION, ORGANIZATIONS & RBAC

### Tenant Architecture
- **Hierarchical Scoping**: `Organization` $\rightarrow$ `Users` (Roles: `ADMIN`, `MANAGER`, `ANALYST`) $\rightarrow$ `Borrowers` $\rightarrow$ `Loans`.
- **JWT Authentication**: Passwords hashed with `bcrypt`. JWT access tokens (30 min expiry) and refresh tokens (7 days expiry).

### Verified Lifecycle Features
- Organization registration & onboarding.
- Member email invitations with secure token verification.
- Dynamic role elevation/demotion (`ADMIN` only).
- Multi-tenant query isolation: Analysts cannot read or mutate cross-organization records.

### Routing & Navigation Guards (Fixed)
- **Public Routes**: `/` (Landing), `/login`, `/register`, `/invite/accept`.
- **Protected App Routes**: `/app/*` (Dashboard, Borrowers, Loans, Risk, Stress Testing, Graph, Copilot, Settings).
- **Navigation Guard**:
  - Authenticated users attempting to visit `/login` or `/register` are automatically redirected to `/app` using `replace: true`.
  - Logging in or registering navigates to `/app` using `navigate("/app", { replace: true })`, preventing the browser "Back" button from trapping users in the login screen.

---

## 6. LANDING PAGE & DESIGN SYSTEM

- **Route**: `/`
- **Visual Identity**: Institutional, clean, dark-themed SaaS aesthetic designed for credit fund managers and institutional risk officers.
- **Iconography**: Clean Lucide React SVG icons throughout (`Building2`, `BarChart3`, `FileText`, `Scale`, `Activity`, `BrainCircuit`, `DollarSign`, `ShieldCheck`). No decorative emojis.
- **Auth-Aware CTAs**:
  - When logged in: Header and Hero display **"Enter Workspace"** / **"Launch Platform"** (navigates directly to `/app`).
  - When logged out: Header and Hero display **"Login"** and **"Get Started"** (navigates to `/login` and `/register`).

---

## 7. BORROWERS, LOANS & ARCHIVAL SYSTEM

### Borrower & Facility Workflow
- Borrowers support company profiles, sector classifications, credit ratings, and primary jurisdictions.
- Loan Facilities track commitment limits, drawn balances, interest rate benchmark spreads, maturity dates, and facility currency.

### Multi-Currency Exposure Fix
- **Previous Issue**: Portfolio Exposure previously hardcoded `$USD` symbols, corrupting facilities issued in other denominations (e.g., INR ₹50M was displayed as $50M).
- **Current Canonical Implementation**:
  - Portfolio aggregate exposure groups facilities **by currency** without applying fake/static FX exchange rates.
  - Formatted accurately with standard international currency symbols:
    - USD: `$109.4B`
    - INR: `₹50.0M`
    - EUR: `€25.0M`
    - IDR: `IDR 10.9T`

### Non-Destructive Archival
- Borrowers and Loans support `is_archived: bool`, `archived_at`, `archived_by`.
- Filtering tabs: `[Active]`, `[Archived]`, `[All]`.
- Archiving a loan immediately removes its covenants and exposure from the active Risk Monitor and Dashboard calculations. Restoring it returns the facility to active monitoring.

---

## 8. DOCUMENT INGESTION & EXTRACTION

### Ingestion Channels
1. **Direct File Upload**: Supports PDF, DOCX, XLSX, CSV, and TXT files via `multipart/form-data`.
2. **SEC Filing URL Ingestion**: Accepts URLs from `sec.gov` and `cloudfront.net` (with strict SSRF domain whitelisting).
3. **Automated Extraction Pipeline**:
   - `DocumentUploadedHandler` chunks documents into semantic blocks.
   - Vectors are computed and upserted to Pinecone.
   - Financial statements (Revenue, EBITDA, Total Debt, Cash, Interest Expense) are extracted.
   - Covenants (Ratio type, Operator, Threshold, Frequency) are extracted and saved to PostgreSQL.
   - Verified that both direct file upload and SEC URL ingestion produce identical extracted financial and covenant metrics for benchmark assets (e.g. Apple 10-Q/Credit Agreement).

---

## 9. RISK MONITOR & COVENANT EVALUATION

### A. Covenant Deduplication
- **Fixed Issue**: Repeated document parsing previously generated duplicate covenant records.
- **Fix**: Implemented strict per-agreement deduplication before insertion and scoped retrieval to active agreement IDs. Active Apple borrower contains exactly **2 monitored covenants** (Maximum Leverage Ratio $\le 3.50\times$, Minimum Interest Coverage $\ge 3.00\times$).

### B. UNKNOWN Status & "None ≠ 0" Rule
> [!IMPORTANT]
> **Strict Financial Semantic Rule**: `None` / `NULL` (unavailable data) is **NEVER** equal to `0.0`.
- If a metric (e.g. EBITDA) is missing, financial ratios depending on EBITDA cannot be computed.
- Covenant status is assigned **`UNKNOWN`** (not `COMPLIANT`, not `BREACHED`).
- Headroom percentage is set to `None` / `NULL` $\rightarrow$ Rendered in UI as **`N/A (Ratio unavailable)`**.

### C. Health Score Canonical Dimensions
The Covenexa Health Score evaluates 5 canonical weighted dimensions:
1. **Financial Performance**: 30%
2. **Covenant Compliance**: 25%
3. **Liquidity**: 20%
4. **Leverage**: 15%
5. **Historical Trend**: 10%

**Dynamic Renormalization**: When one or more components are `None` (e.g., Leverage cannot be computed due to missing EBITDA), the engine dynamically renormalizes the weights across the *available* components so that the score scale remains strictly 0–100.

**Canonical Benchmark (Apple Example)**:
- **Total Health Score**: **`97.1 / 100`** (Rating: `EXCELLENT`)
- **Breakdown**:
  - Financial Performance: `N/A`
  - Covenant Compliance: `100.0`
  - Liquidity: `100.0`
  - Leverage: `N/A`
  - Historical Trend: `84.0` (Calculated prior to composite aggregation)

### D. Default Probability & Prudential Risk
- Evaluates base credit risk + missing data penalties (prudential conservatism).
- Apple Default Probability: `30.0%` (`HIGH` prudential risk category due to missing EBITDA and Interest Expense metrics in quarterly certificate).
- Health Score (operational/liquidity health) and Default Probability (prudential downside risk) represent distinct risk dimensions and intentionally differ.

### E. Idempotency & Relationships
- Recommendations join cleanly: `covenants` $\rightarrow$ `agreements` $\rightarrow$ `loans`.
- Re-running the risk pipeline is completely idempotent (no duplicate recommendation rows).

---

## 10. STRESS TESTING ENGINE

> [!NOTE]
> **EBITDA Slider Decision**: The EBITDA stress-testing slider is intentionally retained in its current working configuration. Do not redesign, remove, or modify it until all deployment milestones are completed.

### Robust Scenario Calculations
When EBITDA is unavailable, the stress engine does **not** crash; it continues to evaluate revenue, debt, and interest shocks:
- **Stressed Revenue** = $\text{Baseline Revenue} \times (1 + \Delta \text{Revenue})$
- **Stressed Debt** = $\text{Baseline Total Debt} \times (1 + \Delta \text{Debt})$
- **Incremental Interest Expense** = $\text{Stressed Debt} \times \Delta \text{Interest Rate (bps / 10,000)}$

### 3-State Facility Resilience UI
1. **`true`**: **"Facility At Risk Under This Scenario"** (Projected breach)
2. **`false`**: **"Facility Remains Resilient"** (Evaluated and passed)
3. **`null`**: **"Unable to Determine Covenant Impact"** (Covenant ratios require unavailable base data)

Simulations are non-destructive and do not mutate baseline SQL records.

---

## 11. AI CREDIT COPILOT

### Architecture & Fixes Applied
- **Account-Isolated Chat History**: Conversations are saved in `copilot_conversations` and `copilot_messages` keyed by `user_id` and `organization_id`. Analysts only view their own private chat sessions.
- **Generation Robustness**: Structured prompt sanitization, temperature control (0.1 for high precision), retry logic on short/empty LLM responses, and deterministic SQL fallback if Cohere API is unavailable.
- **Institutional UI Formatting**:
  - Response text contains clean paragraphs and bullet points.
  - Raw markdown artifacts (e.g. `###`, unrendered `**`, internal UUIDs, raw `None`, `[SOURCE: loan-123]`) are completely scrubbed from answer text.
  - Evidence and document citations appear exclusively in the dedicated **Sources / Evidence Drawer**.

---

## 12. KNOWLEDGE GRAPH

- **Route**: `/app/graph`
- **Topology**: Interactive visual graph displaying Borrowers, Facilities, Agreements, Covenants, and Financial Metrics.
- **Integrity**: Clean node labels (no raw UUIDs, no `NONE`), correct edge counts, dynamic live refresh on borrower switch, and complete archival awareness.

---

## 13. TEST SUITE & VERIFICATION STATUS

- **Backend Pytest Suite**:
  ```bash
  set -a && source .env && set +a && backend/.venv/bin/pytest
  ```
  **Result**: **180 items collected (179 passed, 1 skipped, 0 failed)**.
- **Frontend TypeScript Verification**:
  ```bash
  cd frontend && npx tsc --noEmit
  ```
  **Result**: **0 errors**.
- **Frontend Production Build**:
  ```bash
  cd frontend && npm run build
  ```
  **Result**: **Successful production build (`dist/` generated)**.
- **Source Code Verification**:
  - Zero hardcoded developer-machine paths (`/Users/parvgupta` = 0).
  - All source file lookups use `Path(__file__).resolve().parents[2]`.

---

## 14. DOCKER & CONTAINERIZATION

1. **`backend/Dockerfile`**:
   - Multi-stage image (`python:3.12-slim`).
   - Production target: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]`.
2. **`frontend/Dockerfile`**:
   - Multi-stage image (`node:20-alpine` builder $\rightarrow$ `nginx:alpine` runtime).
   - Serves static assets on port 80 with SPA fallback routing (`try_files $uri $uri/ /index.html;`).
3. **`mcp_server/Dockerfile`**:
   - Runs Model Context Protocol microservice on port 8001.
4. **`docker-compose.yml`**:
   - Local development environment with volume mounts and live reload.

---

## 15. CI/CD WORKFLOWS

### Continuous Integration ([`.github/workflows/ci.yml`](file:///.github/workflows/ci.yml))
- Spawns PostgreSQL 15 and Redis 7 service containers.
- Executes `cd backend && alembic upgrade head` to verify fresh database schema migration.
- Runs full backend pytest suite.
- Runs frontend `npx tsc --noEmit` and `npm run build`.
- Validates production Docker builds for backend and frontend.

### Continuous Deployment ([`.github/workflows/cd.yml`](file:///.github/workflows/cd.yml))
- Triggered by release tags (`v*.*.*`) or manual `workflow_dispatch`.
- Contains Docker build and container registry tagging steps.

---

## 16. SECURITY & SECRETS AUDIT

- `.env` was **never committed to Git history**.
- `.gitignore` rigorously ignores `.env`, `*.env`, `/uploads/`, `/backups/`, `/reports/`.
- No real API keys (Cohere, Pinecone, LlamaParse) or JWT secrets exist in tracked files.
- `Supabase` is **not** used; no Supabase credentials exist.
- All secrets for production must be injected via environment variables in the cloud hosting provider.

---

## 17. PRODUCTION ENVIRONMENT VARIABLES

| Variable Name | Description | Secret? | Example / Format |
| :--- | :--- | :---: | :--- |
| `APP_ENV` | Application environment mode | No | `production` |
| `DATABASE_URL` | PostgreSQL connection string | **Yes** | `postgresql+asyncpg://user:pass@host:5432/covenexa` |
| `JWT_SECRET_KEY` | 256-bit encryption key for JWTs | **Yes** | 64-char hex string (`openssl rand -hex 32`) |
| `REDIS_URL` | Redis connection string | **Yes** | `redis://:password@host:6379/0` (or `rediss://`) |
| `NEO4J_URI` | Neo4j Bolt connection URI | No | `bolt://host:7687` or `neo4j+s://<db>.databases.neo4j.io` |
| `NEO4J_USER` | Neo4j username | No | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | **Yes** | `<password>` |
| `COHERE_API_KEY` | Cohere API Key for LLM & Embed | **Yes** | `prod_cohere_key_...` |
| `PINECONE_API_KEY` | Pinecone Vector DB API Key | **Yes** | `pcsk_...` |
| `PINECONE_ENVIRONMENT` | Pinecone Cloud Region | No | `us-east-1` |
| `PINECONE_INDEX_NAME` | Pinecone Index Name | No | `covenexa-docs` |
| `CORS_ORIGINS` | Allowed Frontend Domain(s) | No | `https://covenexa.vercel.app,https://covenexa.ai` |
| `UPLOAD_DIR` | Directory for uploaded documents | No | `/app/uploads` |
| `VITE_API_BASE_URL` | Frontend API Target URL | No | `https://backend-production-xxxx.up.railway.app` |
| `VITE_APP_NAME` | Frontend App Branding | No | `Covenexa` |
| `VITE_APP_ENV` | Frontend Environment | No | `production` |

---

## 18. PRODUCTION ARCHITECTURE DECISION

Based on explicit user decisions:
- **Frontend Hosting**: **Vercel** (Global CDN, instant Edge SPA routing, automatic preview deployments).
- **Backend Hosting**: **Railway** (High uptime, continuous container execution, no aggressive idle/sleep delays like Render).
  - *Constraint*: **DO NOT USE RENDER for backend**.
- **Relational Database**: Managed PostgreSQL (Railway PostgreSQL, AWS RDS, or Neon).
- **Cache & Event Bus**: Managed Redis (Railway Redis or Upstash).
- **Knowledge Graph**: Neo4j AuraDB (Fully managed cloud instance).
- **Vector Database**: Pinecone Serverless.
- **AI Synthesis**: Cohere Cloud API.
- **Production File Storage**: Persistent Volume mounted to `/app/uploads` on Railway (or Cloudflare R2 / S3 adapter).

---

## 19. MASTER DEPLOYMENT EXECUTION PLAN

```
Phase 1: Backend & Database Deployment (Railway)
  Step 1: Deploy FastAPI Backend Docker container on Railway.
  Step 2: Provision & connect Managed PostgreSQL service.
  Step 3: Execute production database migration: `alembic upgrade head`.
  Step 4: Provision & connect Managed Redis service (`REDIS_URL`).
  Step 5: Provision & connect Neo4j AuraDB instance (`NEO4J_URI`, credentials).
  Step 6: Configure Pinecone Serverless credentials (`PINECONE_API_KEY`).
  Step 7: Configure Cohere API credentials (`COHERE_API_KEY`).
  Step 8: Mount persistent storage volume to `/app/uploads`.
  Step 9: Validate backend health check at `GET https://<railway-url>/health`.

Phase 2: Frontend Deployment (Vercel)
  Step 10: Deploy React/Vite SPA on Vercel.
  Step 11: Set `VITE_API_BASE_URL=https://<railway-url>`.
  Step 12: Configure `CORS_ORIGINS=https://<vercel-domain>` on Railway backend.

Phase 3: Production E2E Verification & Hand-off
  Step 13: Execute full end-to-end user journey on production domains.
  Step 14: Finalize CI/CD webhooks.
  Step 15: Run production regression verification.
```

---

## 20. ENGINEERING PREFERENCES & SAFETY RULES

1. **Step-by-Step Action**: Provide exact, actionable instructions one phase at a time; never overwhelm the user with 20 simultaneous instructions.
2. **Preserve Validated Functionality**: Do not rewrite working application/financial logic.
3. **No Supabase / No Render**: Strictly follow architectural constraints.
4. **No Emojis in Core UI**: Maintain institutional, high-finance styling with Lucide icons.
5. **Post-Deployment Reminder**: After all deployment steps succeed and production verification is complete, prompt the user with:
   > *"Now let's revisit the EBITDA stress slider."*

---

## 21. CURRENT IMMEDIATE NEXT ACTION

👉 **Deploy Covenexa FastAPI Backend to Railway.**
Begin by setting up the Railway project, attaching the GitHub repository, and provisioning PostgreSQL and Redis.
