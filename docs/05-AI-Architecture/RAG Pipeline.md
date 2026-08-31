# RAG Pipeline — Hybrid GraphRAG Architecture

## Overview

Covenexa uses a **Hybrid GraphRAG** pipeline that combines three distinct retrieval sources before generating any AI response. This approach grounds every answer in actual portfolio data rather than LLM parametric knowledge.

---

## The Three Retrievers

### 1. SQL Retriever (`ai/rag/retrievers/sql_retriever.py`)
Queries PostgreSQL directly for structured borrower data:
- Borrower profile (name, sector, country, risk level)
- Latest Borrower Health Score and category
- Active covenant compliance status and headroom values
- Latest financial metrics (EBITDA, leverage, coverage ratios)
- AI recommendations and alerts

**When used:** Always included for the active Borrower context.

### 2. Vector Retriever (`ai/rag/retrievers/vector_retriever.py`)
Queries Pinecone using Cohere Embed v4 embeddings:
- Converts user query to a 1024-dimension embedding
- Filters by `borrower_id` namespace to enforce tenant isolation
- Returns top-k semantically similar document chunks from ingested agreements
- Zero results do NOT fall back to unfiltered search (strict isolation)

**When used:** When document-level context is needed (covenant clauses, agreement text).

### 3. Graph Retriever (`ai/rag/retrievers/graph_retriever.py`)
Queries Neo4j for entity relationship context:
- Traverses Borrower → Loan → Agreement → Covenant nodes
- Returns relationship paths and connected entity attributes

**When used:** When relationship mapping context is needed (e.g., "which covenants apply to which facility").

---

## Retrieval Pipeline Flow

```
User Query (natural language)
         │
         ▼
  RetrieverFactory.get_retriever()
         │
         ├──► SQL Retriever       → borrower profile, health, financials, covenants
         ├──► Vector Retriever    → top-k matching document chunks from Pinecone
         └──► Graph Retriever     → entity relationship paths from Neo4j
         │
         ▼
  HybridRetriever.retrieve()     → merges all three context sources
         │
         ▼
  ContextBuilder.build()         → formats merged context into LLM prompt
         │
         ▼
  Cohere Command A (LLM)         → synthesis + response generation
         │
         ▼
  CopilotAgent response          → { response: str, citations: list }
```

---

## Context Builder (`ai/rag/context_builder.py`)

Formats the merged retrieval results into a structured prompt:

```
[BORROWER CONTEXT]
Company: {company_name} | Sector: {sector} | Country: {country}
Health Score: {score}/100 ({category})
Leverage: {debt_to_ebitda}x | Coverage: {interest_coverage}x

[COVENANT COMPLIANCE]
- {covenant_name}: {actual_value} vs {threshold} → {status}

[FINANCIAL METRICS]
Revenue: ${revenue}M | EBITDA: ${ebitda}M | Debt: ${total_debt}M

[DOCUMENT EVIDENCE]
Chunk 1: "{chunk_text}"
Chunk 2: "{chunk_text}"
...

[ANALYST QUERY]
{user_question}
```

---

## Tenant Isolation

Pinecone is partitioned by `agreement_id` as the namespace. Every embed query includes a `filter: { borrower_id: "..." }` metadata filter to ensure no cross-borrower data leakage.

---

## Anti-Hallucination Measures

| Measure | Implementation |
|:--------|:--------------|
| Context-only generation | LLM is instructed to only use retrieved context |
| Citations required | Response must reference source data points |
| Zero-result handling | Vector retriever returns empty rather than falling back to all-namespace search |
| `None ≠ 0` enforcement | Missing metrics shown as `N/A`, not fabricated as zero |
| Mock fallback | If no Cohere API key, returns a deterministic structured mock response |

---

## Pinecone Index Configuration

- **Index name:** `covenexa-docs`
- **Dimension:** 1024 (Cohere Embed v4)
- **Metric:** Cosine similarity
- **Namespace:** Per `agreement_id`
- **Metadata fields:** `borrower_id`, `agreement_id`, `chunk_index`, `chunk_type`