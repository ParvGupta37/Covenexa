# Case Study — Covenexa

## The Problem

Private credit fund managers and direct lenders face a critical but unglamorous operational challenge: **covenant monitoring**. Every loan agreement contains dozens of financial and operational covenants — rules the borrower must follow. Manually tracking these across a portfolio of 30–100 borrowers using spreadsheets is slow, error-prone, and reactive. Covenant breaches are often discovered weeks after they occur — by which point the lender has lost leverage.

The existing market solutions (loan management software, document management platforms, BI tools) are all either too generic or too siloed. None offer automated covenant extraction from legal documents, AI-powered health scoring, or proactive risk recommendations.

---

## The Solution

**Covenexa** is an AI-native SaaS platform that turns loan agreements and financial statements into a continuously monitored, AI-analyzed risk intelligence system.

The core innovation is combining three technologies that have never been productized together for private credit:
1. **LLM-powered document intelligence** — extract structured covenant data from unstructured PDFs
2. **Multi-agent financial analysis** — compute health scores, flag covenant breaches, generate recommendations
3. **Hybrid GraphRAG** — answer natural language questions about any borrower with evidence from SQL, vectors, and knowledge graphs

---

## Technical Architecture

### The Challenge: Unstructured → Structured → Intelligent

Loan agreements are 80–300 page legal documents. Financial statements are messy PDFs or SEC HTML filings. The challenge was building an automated pipeline that could ingest either format, extract relevant data with high accuracy, and produce actionable risk intelligence — without hardcoded rules.

**Solution:** A LangGraph multi-agent document workflow:
```
Upload → DocumentAgent (chunk + embed) → CovenantAgent (LLM extract) → FinancialAgent (LLM extract) → RiskPipeline (compute scores + alerts)
```

### The Challenge: Deterministic Finance vs. Probabilistic AI

Financial computations must be exact. You cannot allow an LLM to "estimate" a Debt/EBITDA ratio. But covenant monitoring also requires understanding the semantic meaning of complex legal covenant language.

**Solution:** Strict separation between the **Engine layer** (deterministic math: ratios, health scores, stress tests) and the **Agent layer** (LLM tasks: extraction, copilot, recommendations).

### The Challenge: Multi-Tenant Vector Search

Using Pinecone as a shared vector database for all borrowers creates tenant isolation risk. A poorly formed vector query could retrieve document chunks from a different borrower.

**Solution:** Pinecone namespace-per-agreement + mandatory `borrower_id` metadata filter on every query. Zero-result responses do not retry without the filter.

### The Challenge: Meaningful AI Answers

Generic RAG systems produce answers grounded in documents but blind to current financial state. A lender asking "Is this borrower at risk?" needs context from both the legal agreements AND the latest financial metrics.

**Solution:** Hybrid GraphRAG — three retrieval sources combined before every LLM call:
- SQL: current health score, financial ratios, covenant compliance
- Pinecone: relevant document chunks (legal agreement context)
- Neo4j: entity relationship context (which loans have which covenants)

---

## Implementation Highlights

| Highlight | Detail |
|:----------|:-------|
| 92-test backend suite | 100% pass, all without real API keys |
| `None ≠ 0` data integrity | Unanalyzed fields never fabricated as zero |
| Path traversal protection | Filenames sanitized on upload |
| SSRF prevention | SEC EDGAR URL allowlist blocks internal network access |
| Production readiness | Dev vs. prod error exposure differentiation |
| Accumulating risk history | Health scores and risk assessments accumulate for trend analysis |
| Event-driven architecture | Redis Pub/Sub decouples uploads from AI processing |

---

## What I Learned

1. **Domain modeling matters more than frameworks.** Designing the 19-table schema with clear ownership boundaries (accumulate vs. replace) prevented countless data integrity bugs.
2. **LLMs need deterministic guardrails.** Mixing LLM extraction with deterministic computation engines was the right architecture — not end-to-end LLM.
3. **Tenant isolation in AI systems is hard.** Vector databases and graph databases both require deliberate isolation strategies that are easy to get wrong.
4. **`None ≠ 0` is a philosophy, not a line of code.** Every data pipeline decision needs this question: "Is this value actually zero, or just unknown?"
5. **Test your security invariants explicitly.** Don't assume SSRF, path traversal, or tenant isolation is handled — write a test for each.

---

## Outcome

A production-ready AI platform that demonstrates:
- Full-stack engineering (backend + frontend + AI + databases)
- Complex AI system design (multi-agent, RAG, knowledge graph)
- Enterprise engineering practices (DDD, testing, security, audit logging)
- Domain expertise in private credit / fintech
