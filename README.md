# Covenexa — AI-Native Private Credit Risk & Covenant Intelligence Platform

Covenexa is an enterprise AI credit intelligence platform for private credit lenders, institutional credit officers, and portfolio managers. It automates credit risk evaluation, covenant compliance monitoring, SEC EDGAR document ingestion, and conversational Q&A using an active **Hybrid GraphRAG** architecture.

---

## Key Capabilities

1. **Active Hybrid GraphRAG Engine**:
   - **PostgreSQL**: Authoritative structured financial metrics, leverage ratios, and covenant monitoring statuses.
   - **Pinecone**: Vector similarity search over SEC EDGAR filings and credit agreement text passages using Cohere 1024-dimensional embeddings (`embed-english-v3.0`).
   - **Neo4j**: Knowledge Graph traversal across Borrower ──► Loan ──► Agreement ──► Covenant ──► Risk relationships.
2. **Deterministic Risk Intelligence Pipeline**:
   - **HealthScoreEngine**: Multi-factor borrower health scoring (0–100) with historical trend tracking (`None` / `N/A` for first-run data).
   - **DefaultPredictor**: Evidence-grounded default probability estimation with explicit 5.0% baseline transparency.
   - **CovenantMonitor**: Automated ratio monitoring against maintenance thresholds using extracted covenant formulas.
   - **RecommendationEngine**: Idempotent, non-redundant credit action recommendations.
3. **Document & SEC Ingestion Pipeline**:
   - Direct PDF/DOCX credit agreement upload parsing.
   - Live SEC EDGAR filing ingestion with strict URL validation and User-Agent headers.
4. **Conversational AI Copilot**:
   - Cohere Command model synthesis grounded strictly in retrieved multi-source evidence citations (`[PostgreSQL]`, `[Pinecone]`, `[Neo4j]`).
5. **Executive Credit Memorandum Generation**:
   - Automated memo generation with complete data integrity (preserving `None` / `N/A` semantics for un-analyzed borrowers).

---

## System Architecture

```
User / Frontend (React + TypeScript)
       │
       ▼
FastAPI Backend (Async SQLAlchemy + Pydantic v2 + JWT RBAC)
       │
  ┌────┼───────────────────────────┐
  │    │                           │
  ▼    ▼                           ▼
PostgreSQL (Authoritative)  Pinecone (Vector 1024-dim)  Neo4j (Knowledge Graph)
  │    │                           │
  └────┴─────────────┬─────────────┘
                     │
                     ▼
          Hybrid Retriever Factory
                     │
                     ▼
           Cohere Command LLM
```

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (Asyncpg), Pydantic v2, Structlog
- **Databases**: PostgreSQL 17, Neo4j 5 (Bolt), Redis 7, Pinecone Vector Database
- **AI/LLM**: Cohere Command (`command-a-03-2025`), Cohere Embed (`embed-english-v3.0`, 1024 dimensions)
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS, Lucide Icons, Recharts, Zustand
- **Event Bus**: Redis Pub/Sub Event Bus

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Neo4j 5+ (optional, degrades gracefully if offline)
- Redis 6+

### Environment Configuration

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

Configure required service credentials in `.env`:
```env
DATABASE_URL=postgresql+asyncpg://covenexa_user:covenexa_pass@localhost:5432/covenexa
COHERE_API_KEY=your_cohere_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=covenexa-docs
NEO4J_URI=bolt://localhost:7687
```

### Backend Setup

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run database migrations:
```bash
alembic upgrade head
```

Run backend dev server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will run on `http://localhost:5173`.

---

## Running Tests & Type Checks

### Backend Unit & Integration Tests (Pytest)
```bash
cd backend
source .venv/bin/activate
PYTHONPATH=..:. pytest tests/ -v
```

### Frontend TypeScript Verification
```bash
cd frontend
npx tsc --noEmit
```

---

## Security & Tenant Isolation Rules

1. **Tenant Isolation**: Vector retrieval for a specific borrower strictly filters by `borrower_id` in Pinecone metadata. If no chunks exist, an empty list `[]` is returned (no cross-tenant fallback).
2. **Path Traversal Protection**: Uploaded filenames are sanitized with `os.path.basename()` before writing to local disk volumes.
3. **SSRF Protection**: SEC EDGAR URL ingestion enforces strict `urllib.parse` domain parsing against allowed domains (`sec.gov`, `cloudfront.net`).
4. **Data Integrity (`None ≠ 0`)**: Missing or uncalculated financial metrics, health scores, and default probabilities remain `None` internally and display as `"N/A"` in UI/reports. Legitimate measured zero values remain `0`.
5. **RBAC**: All credit entity endpoints (`/borrowers/`, `/organizations/`, `/loans/`, `/documents/`, `/risk/`, `/reports/`) require authenticated JWT Bearer tokens with authorized roles (`ADMIN`, `MANAGER`, `ANALYST`).
