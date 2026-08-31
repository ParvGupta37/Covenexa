# High Level Architecture

## System Overview

Covenexa is a **modular, AI-native SaaS platform** composed of five layers that work together to transform raw legal and financial documents into portfolio-wide risk intelligence.

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                     │
│  Dashboard | Risk | Copilot | Docs | Stress | Graph      │
└────────────────────────┬────────────────────────────────┘
                         │ REST API (Axios + JWT)
┌────────────────────────▼────────────────────────────────┐
│               BACKEND API (FastAPI / DDD)                │
│  Auth | Orgs | Borrowers | Loans | Uploads | Risk |      │
│  Documents | Copilot | Alerts | Audit | Reports          │
└──────────┬──────────────────────────┬───────────────────┘
           │ Redis Event Bus           │ Direct import
           │ (Document uploads)        │ (Risk engine calls)
┌──────────▼──────────┐    ┌──────────▼────────────────────┐
│  AI WORKFLOW LAYER  │    │     AI ENGINE LAYER            │
│  (LangGraph)        │    │  (Deterministic Computation)   │
│                     │    │                                │
│  DocumentWorkflow   │    │  FinancialEngine               │
│  ComplianceWorkflow │    │  HealthScoreEngine             │
│  ├ DocumentAgent    │    │  DefaultPredictor              │
│  ├ CovenantAgent    │    │  CovenantMonitor               │
│  ├ FinancialAgent   │    │  RecommendationEngine          │
│  └ RiskPipeline     │    │  StressTester                  │
│                     │    │  AlertEngine                   │
│  CopilotAgent (RAG) │    │  PipelineRunner                │
└──────────┬──────────┘    └────────────────────────────────┘
           │ Read/Write
┌──────────▼──────────────────────────────────────────────┐
│                    DATA LAYER                            │
│  PostgreSQL (19 tables) | Pinecone | Neo4j | Redis       │
└─────────────────────────────────────────────────────────┘
           │ External APIs
┌──────────▼──────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                        │
│  Cohere (LLM + Embed) | SEC EDGAR | Pinecone Cloud       │
└─────────────────────────────────────────────────────────┘
```

---

## Core Subsystems

### 1. Document Intelligence
**Trigger:** User uploads PDF/DOCX or submits SEC EDGAR URL

**Flow:**
```
Upload → Redis event → DocumentWorkflow (LangGraph)
  → DocumentAgent: parse + chunk + embed → Pinecone
  → CovenantAgent: LLM extraction → covenants table
  → FinancialAgent: LLM extraction → financial_metrics table
  → RiskIntelligencePipeline (auto-trigger)
```

### 2. Risk Intelligence Pipeline
**Trigger:** After document analysis, or manually via API

**Flow:**
```
FinancialEngine → compute 7 ratios
CovenantMonitor → evaluate compliance (DELETE + INSERT)
HealthScoreEngine → 0–100 composite score (INSERT)
DefaultPredictor → Altman Z-Score → default probability (INSERT)
RecommendationEngine → prioritized actions (INSERT)
AlertEngine → INSERT alerts for breaches
```

### 3. Hybrid GraphRAG (AI Copilot)
**Trigger:** User query via Copilot interface

**Flow:**
```
User query
  → SQL Retriever: borrower profile + health + financials + covenants
  → Vector Retriever: Pinecone semantic search (top-k chunks)
  → Graph Retriever: Neo4j entity relationships
  → ContextBuilder: merge into structured prompt
  → Cohere Command A: synthesize response + citations
```

### 4. Portfolio Dashboard
**Data source:** All aggregated at query time from PostgreSQL

- Health score: latest `borrower_health_scores` per borrower → avg
- High risk count: `borrower_health_scores` where category IN ('HIGH_RISK', 'CRITICAL')
- Covenants at risk: `covenant_monitoring` where status IN ('breach', 'critical')
- Alerts: `alerts` where is_read = false
- Exposure: SUM of `loans.principal_amount` where status = 'ACTIVE'

---

## Key Design Decisions

| Decision | Rationale |
|:---------|:----------|
| DDD (Domain-Driven Design) | Clean layer separation prevents spaghetti code as complexity grows |
| Event bus for uploads | Decouples upload API response from heavy AI processing |
| Engine vs. Agent separation | Financial math is deterministic; LLM is for language tasks only |
| Accumulate health/risk history | Enables trend analysis without losing historical data |
| Replace covenant_monitoring | Always reflects current state; avoids stale compliance records |
| None ≠ 0 policy | Prevents misleading dashboard metrics for unanalyzed borrowers |
| Single FastAPI process | v1.0 simplicity; horizontally scalable in production with multiple workers |