# Sprint 3 — Risk Intelligence & AI Copilot

## Sprint Goal

Build the full risk intelligence system: financial ratio computation, Borrower Health Score (5-dimension composite), Altman Z-Score default prediction, covenant compliance monitoring, portfolio stress testing, AI recommendations, automated alerts, and the Hybrid GraphRAG AI Copilot.

**Exit Criteria:** For any analyzed borrower, users can view health score, covenant compliance, run stress scenarios, get AI recommendations, and ask natural language questions via Copilot.

---

## Objectives Completed

- [x] PostgreSQL schema — Wave 3: borrower_health_scores, risk_assessments, covenant_monitoring, alerts, stress_test_results, ai_recommendations
- [x] Alembic migration (`0003_risk_intelligence.py`)
- [x] FinancialEngine — 7 ratio calculations (debt/ebitda, coverage, current ratio, gross margin, etc.)
- [x] HealthScoreEngine — 0–100 composite score with 5 weighted dimensions
- [x] DefaultPredictor — Altman Z-Score → 0–100% default probability
- [x] CovenantMonitor — evaluate all covenants (DELETE + INSERT per pipeline run)
- [x] RecommendationEngine — CRITICAL/HIGH/MEDIUM/LOW prioritized actions
- [x] AlertEngine — INSERT alerts on covenant breach or health decline
- [x] RiskIntelligencePipeline (PipelineRunner) — orchestrates all 6 engines in sequence
- [x] Auto-trigger pipeline after DocumentWorkflow completes
- [x] Lazy pipeline trigger on GET /risk/health if no score but metrics exist
- [x] Risk API endpoints (`/risk/health`, `/risk/default`, `/risk/covenants`, `/risk/stress`, `/risk/recommendations`, `/risk/graph`, `/risk/pipeline`)
- [x] StressTester — apply % shocks to financial inputs, evaluate covenant resilience
- [x] RAG infrastructure: Vector Retriever, Graph Retriever, SQL Retriever, HybridRetriever, ContextBuilder
- [x] CopilotAgent — SQL context + Cohere Command A synthesis + citations
- [x] Copilot API (`POST /copilot/query`)
- [x] Knowledge Graph API (`GET /risk/graph/{borrower_id}`) — nodes + edges from PostgreSQL
- [x] Alerts API (`GET /alerts/`, `POST /alerts/{id}/read`)
- [x] RiskPage, StressTestPage, GraphPage, CopilotPage in frontend
- [x] Dashboard KPIs wired to live database data (no hardcoded fallbacks)

---

## Key Sprint 3 Decisions

| Decision | Detail |
|:---------|:-------|
| Engine layer separate from Agent layer | Financial math must be deterministic; LLM is for language only |
| covenant_monitoring DELETE + INSERT | Always reflects current state; avoids stale records |
| health_scores ACCUMULATE | Enables trend analysis over time |
| Lazy pipeline trigger | Better UX — risk score available without manual pipeline trigger |
| Knowledge Graph from PostgreSQL | Neo4j connected but graph data served from PostgreSQL in v1.0 for stability |
| CopilotAgent SQL-only context | Pinecone + Neo4j retrieval available but not wired in v1.0 — shipped with SQL context for reliability |
