# Resume Points — Covenexa

> Use these bullet points in a resume, LinkedIn, or portfolio context. Tailor to the role.

---

## One-Line Summary

> Built **Covenexa** — an AI-native SaaS platform for private credit portfolio intelligence, featuring multi-agent document analysis, hybrid GraphRAG, real-time covenant monitoring, and automated risk reporting.

---

## Project Description (2–3 Lines)

> Covenexa is a full-stack B2B fintech platform that ingests loan agreements and financial statements, extracts covenants using LLMs (Cohere Command A), scores borrower health on a 0–100 composite scale, and provides an AI Copilot powered by Hybrid GraphRAG (SQL + Pinecone vectors + Neo4j graph). Built with FastAPI, React, PostgreSQL, and a LangGraph multi-agent orchestration system.

---

## Technical Bullet Points

**AI / ML**
- Designed and implemented a **10-agent multi-agent system** using LangGraph with specialized agents for document parsing, covenant extraction, financial analysis, compliance checking, recommendations, and report generation
- Built a **Hybrid GraphRAG pipeline** combining SQL retrieval (PostgreSQL), semantic search (Pinecone + Cohere Embed v4), and knowledge graph traversal (Neo4j) with strict per-borrower tenant isolation
- Engineered a **Borrower Health Score** (0–100) with 5 weighted dimensions — financial performance, compliance, liquidity, leverage, and trend — using deterministic engine computation
- Implemented **Altman Z-Score** based default probability prediction with custom mapping to 0–100% scale
- Integrated **LLM-powered covenant extraction** from legal PDFs, producing structured data (metric, threshold, operator) with no hardcoded fallbacks

**Backend**
- Architected a **Domain-Driven Design (DDD) FastAPI backend** across 4 layers: API, Application, Domain, Infrastructure — with clean separation of concerns
- Designed a **19-table PostgreSQL schema** across 4 migration waves, with cascading deletes, accumulating risk history, and clear entity ownership
- Implemented **asynchronous document processing** using a Redis Pub/Sub event bus — decoupling uploads from AI pipelines
- Built **SEC EDGAR integration** for direct URL-based financial filing ingestion with SSRF protection

**Frontend**
- Built a **React 18 + TypeScript + Vite** enterprise SaaS dashboard from scratch with custom CSS design system (no framework)
- Implemented **Zustand global state** with cross-page borrower context persistence via localStorage
- Designed and integrated **Recharts data visualizations**: portfolio health donut, facility exposure bar chart, health score sparklines

**Security & Production Readiness**
- Enforced **JWT authentication** (HS256, access + refresh tokens) with bcrypt password hashing and role-based access control (ADMIN / ANALYST)
- Maintained **92-test suite (100% pass)** covering engine accuracy, GraphRAG retrieval, security invariants, and production readiness
- Implemented **`None ≠ 0` data integrity policy** — unanalyzed values returned as `null`, never fabricated as zero
- Applied **input sanitization** for path traversal attacks, SSRF prevention, and strict tenant isolation in vector queries

---

## Technologies Used

`FastAPI` · `PostgreSQL` · `SQLAlchemy (async)` · `Alembic` · `Pydantic v2` · `Redis` · `Cohere Command A` · `Cohere Embed v4` · `LangGraph` · `LangChain` · `Pinecone` · `Neo4j` · `React 18` · `TypeScript` · `Vite` · `Zustand` · `Recharts` · `Docker` · `pytest` · `JWT` · `bcrypt`

---

## Quantifiable Achievements

- 92 backend tests — 100% pass rate
- 19-table relational schema with 4 migration layers
- 10 specialized AI agents orchestrated via LangGraph
- 3-source hybrid retrieval: SQL + Vector (Pinecone) + Graph (Neo4j)
- 5-dimension Health Score with weighted composite scoring
- <200ms avg response for risk intelligence API endpoints (local)
- Full end-to-end flow: PDF upload → LLM extraction → Risk scoring → AI Copilot in one platform
