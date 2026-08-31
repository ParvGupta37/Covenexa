# Copilot Agent

## Purpose

Answer natural language questions about any borrower using Hybrid GraphRAG — combining real-time financial data from PostgreSQL, semantic document search from Pinecone, and entity relationship context from Neo4j.

---

## File

`ai/agents/copilot_agent.py`

---

## Inputs

```python
{
  "query": str,           # User's natural language question
  "borrower_id": str,     # UUID of the active borrower
  "session_id": str       # Optional conversation session ID
}
```

---

## Processing Flow

```
1. SQL Retriever
   → Fetch borrower profile (name, sector, country, risk_level)
   → Fetch latest health score + category
   → Fetch covenant compliance status (all covenants)
   → Fetch latest financial_metrics (EBITDA, leverage, coverage)
   → Fetch latest AI recommendations

2. Vector Retriever (Pinecone)
   → Embed the user query via Cohere Embed v4
   → Query Pinecone with borrower_id filter + agreement namespaces
   → Return top-5 matching document chunks

3. Graph Retriever (Neo4j)
   → Traverse Borrower → Loan → Agreement → Covenant paths
   → Return entity relationship context

4. ContextBuilder
   → Merge all three retrieval results into a structured prompt

5. Cohere Command A (LLM)
   → Generate a response using ONLY the retrieved context
   → Include citations referencing the source data

6. Return { response: str, citations: list }
```

---

## Outputs

```json
{
  "response": "The leverage covenant requires Debt/EBITDA ≤ 4.0x. The borrower's current ratio is 3.2x, giving headroom of 0.8x (20%). The covenant is currently compliant.",
  "citations": [
    "Source: Financial Metrics (Q4 2025) — Debt/EBITDA: 3.2x",
    "Source: Loan Agreement (Section 7.2) — Leverage covenant threshold: 4.0x"
  ]
}
```

---

## Mock Fallback

If no `COHERE_API_KEY` is set in the environment, the agent returns a deterministic structured response built from SQL data only — without LLM synthesis. This enables development and testing without paid API credentials.

---

## v1.0 Limitation

The Vector Retriever (Pinecone) and Graph Retriever (Neo4j) are implemented but not yet wired into the CopilotAgent response in v1.0. The agent currently uses **SQL context only**. Full Hybrid GraphRAG is planned for v1.1.