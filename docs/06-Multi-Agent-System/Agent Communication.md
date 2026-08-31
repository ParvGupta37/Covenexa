# Multi-Agent System — Architecture Overview

## Design Philosophy

Covenexa's AI backend is decomposed into **10 specialized agents**, each owning a single responsibility. Agents are orchestrated using **LangGraph** (stateful directed graphs) and communicate via structured state objects — not direct function calls.

---

## Agent Registry

| Agent | File | Responsibility |
|:------|:-----|:--------------|
| **DocumentAgent** | `ai/agents/document_agent.py` | Parse, chunk, embed documents → Pinecone |
| **CovenantAgent** | `ai/agents/covenant_agent.py` | LLM extraction of covenant clauses from chunks |
| **FinancialAgent** | `ai/agents/financial_agent.py` | LLM extraction of financial metrics from chunks |
| **CopilotAgent** | `ai/agents/copilot_agent.py` | Hybrid RAG — answer user queries with citations |
| **ComplianceAgent** | `ai/agents/compliance_agent.py` | Validate financial metrics against covenant thresholds |
| **RecommendationAgent** | `ai/agents/recommendation_agent.py` | Prioritize and surface credit action items |
| **ReportingAgent** | `ai/agents/reporting_agent.py` | Generate 6-section Executive Credit Memo |
| **PlannerAgent** | `ai/agents/planner_agent.py` | Route complex queries to the right sub-agent |
| **PortfolioAgent** | `ai/agents/portfolio_agent.py` | Portfolio-level risk aggregation and summary |
| **BaseAgent** | `ai/agents/base_agent.py` | Abstract base class — shared run() interface |

---

## Document Intelligence Workflow (LangGraph)

**File:** `ai/workflows/document_workflow.py`

```
START
  │
  ▼
DocumentAgent
  → Parse PDF/DOCX via LlamaIndex
  → Split into overlapping chunks (1000 tokens, 200 overlap)
  → Embed each chunk via Cohere Embed v4
  → Upsert to Pinecone (namespace = agreement_id)
  → Save DocumentChunk rows to PostgreSQL
  │
  ▼
CovenantAgent
  → For each chunk: LLM prompt to extract covenant clauses
  → Parse: name, metric, threshold, operator, description
  → INSERT into covenants table (keyed to agreement + borrower)
  │
  ▼
FinancialAgent
  → For each chunk: LLM prompt to extract financial figures
  → Parse: revenue, EBITDA, debt, cash, interest expense, ratios
  → INSERT into financial_metrics table
  │
  ▼
Auto-trigger: RiskIntelligencePipeline
END
```

---

## Compliance Workflow

**File:** `ai/workflows/compliance_workflow.py`

```
START
  │
  ▼
ComplianceAgent
  → For each covenant: fetch actual_value from financial_metrics
  → Evaluate: does actual_value violate the operator + threshold?
  → Compute headroom: (threshold - actual) / threshold
  → Assign status: compliant | watch | breach | critical
  → DELETE existing covenant_monitoring for borrower → INSERT fresh rows
END
```

---

## Agent Communication Pattern

Agents do **not** call each other directly. They communicate through:

1. **Shared LangGraph state** — structured dict passed between nodes in a workflow
2. **PostgreSQL** — agents write to DB; downstream agents read from DB
3. **Redis Event Bus** — `DocumentUploadedEvent` triggers the DocumentWorkflow asynchronously

---

## Shared Memory & Context (`ai/memory/`)

- Agent sessions are stored in-memory during a workflow run
- No persistent agent memory across requests (stateless between sessions)
- LangGraph checkpointing is available but not configured for persistence in v1.0

---

## Engine Layer (Non-Agent Computation)

Separate from agents, the **Engine** layer in `ai/engines/` handles deterministic financial computation:

| Engine | File | Computation |
|:-------|:-----|:-----------|
| FinancialEngine | `financial_engine.py` | Compute 7 financial ratios |
| HealthScoreEngine | `health_score_engine.py` | 0–100 composite score (5 dimensions) |
| DefaultPredictor | `default_predictor.py` | Altman Z-Score → 0–100% default probability |
| CovenantMonitor | `covenant_monitor.py` | Evaluate all covenants for a borrower |
| RecommendationEngine | `recommendation_engine.py` | Generate prioritized action items |
| StressTester | `stress_tester.py` | Simulate financial shocks |
| AlertEngine | `alert_engine.py` | Create alerts on threshold breach |
| PipelineRunner | `pipeline_runner.py` | Orchestrate full risk intelligence pipeline |