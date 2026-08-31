# Technology Stack

## AI Stack

| Technology | Role | Version / Notes |
|:-----------|:-----|:----------------|
| **Cohere Command A** | Primary LLM for generation, covenant extraction, financial extraction, copilot synthesis | Cohere Python SDK v5 |
| **Cohere Embed v4** | Document chunk embeddings for Pinecone vector search | `embed-english-v3.0` |
| **LangGraph** | Multi-agent workflow orchestration — stateful directed graphs | Used in `DocumentWorkflow`, `ComplianceWorkflow` |
| **LangChain** | Agent tooling, prompt templates, chain composition | Used as LangGraph dependency |
| **LlamaIndex** | Document parsing, chunking, node extraction | Used in `DocumentAgent` |
| **Pinecone** | Managed vector database — semantic search over document chunks | Index: `covenexa-docs` |
| **Neo4j** | Graph database — entity relationships (Borrower → Loan → Covenant) | Connected; graph API served from PostgreSQL in v1.0 |

---

## Backend Stack

| Technology | Role | Version |
|:-----------|:-----|:--------|
| **FastAPI** | Async REST API framework | Latest |
| **SQLAlchemy** | Async ORM for PostgreSQL | v2 async |
| **Alembic** | Database migrations | 4 migration files (0001–0004) |
| **Pydantic v2** | Request/response validation and domain schemas | v2 |
| **Passlib + bcrypt** | Password hashing | |
| **PyJWT** | JWT token generation and validation | |
| **Structlog** | Structured JSON logging | |
| **Redis (aioredis)** | Async pub/sub event bus | Channel: `DocumentUploadedEvent` |
| **asyncpg** | Async PostgreSQL driver | |
| **httpx** | Async HTTP client for SEC EDGAR downloads | |
| **uvicorn** | ASGI server | |

---

## Frontend Stack

| Technology | Role | Version |
|:-----------|:-----|:--------|
| **React 18** | UI component framework | |
| **TypeScript** | Static typing | |
| **Vite** | Build tool and dev server | v5 |
| **Zustand** | Global state management (`auth.store`, `company.store`) | |
| **React Router v6** | Client-side routing | |
| **Axios** | HTTP client with auth interceptors | |
| **Recharts** | Data visualization (Donut chart, Bar chart, Sparklines) | |
| **Lucide React** | Icon library | |
| **Vanilla CSS** | Styling (no TailwindCSS) | Custom design system in `globals.css` |

---

## Database Stack

| Technology | Role |
|:-----------|:-----|
| **PostgreSQL** | Primary relational database — all business data (19 tables) |
| **Pinecone** | Vector store — document chunk embeddings |
| **Neo4j** | Graph database — knowledge graph for entity relationships |
| **Redis** | Event bus (pub/sub) + session/cache layer |

---

## Infrastructure

| Technology | Role |
|:-----------|:-----|
| **Docker + Docker Compose** | Service orchestration for local development |
| **PostgreSQL container** | `covenexa_db` service |
| **Redis container** | `covenexa_redis` service |
| **Neo4j container** | `covenexa_neo4j` service |
| **Nginx** (optional) | Reverse proxy for production |

---

## External Integrations

| Service | Purpose |
|:--------|:--------|
| **Cohere API** | LLM + Embeddings |
| **Pinecone API** | Vector similarity search |
| **SEC EDGAR** | Public financial filing ingestion via URL |
| **Neo4j Aura** (or local) | Knowledge graph queries |

---

## Developer Tools

| Tool | Purpose |
|:-----|:--------|
| **pytest + pytest-asyncio** | Backend test suite — 92 tests, 100% pass rate |
| **Alembic** | Schema migrations |
| **npx tsc --noEmit** | Frontend TypeScript type checking |
| **Makefile** | Common dev commands (`make dev`, `make test`, `make migrate`) |