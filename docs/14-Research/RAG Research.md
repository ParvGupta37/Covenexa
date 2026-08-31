# RAG Research Notes

## RAG Variants Used in Covenexa

### 1. Basic RAG (Standard)
- Embed query → vector search → retrieve chunks → generate
- Used as baseline in VectorRetriever

### 2. SQL-RAG (Structured RAG)
- Query structured DB → retrieve tabular context → generate
- Used in SQLRetriever for financial metrics and covenant compliance

### 3. GraphRAG
- Query knowledge graph → retrieve entity relationships → enrich context → generate
- Used in GraphRetriever (Neo4j, planned for v1.1)

### 4. Hybrid GraphRAG (Covenexa's approach)
- Combine all three: SQL + Vector + Graph
- Each retriever provides a different "lens" on the borrower data
- ContextBuilder merges all three before LLM call

## Why Hybrid?

| Source | What it knows |
|:-------|:-------------|
| SQL | Current financial state, health score, covenant compliance |
| Vector (Pinecone) | What the legal agreement actually says |
| Graph (Neo4j) | How entities relate — which loans have which covenants |

A question like "Is this borrower's leverage covenant at risk?" needs all three:
- SQL: current debt/ebitda ratio → 3.8x
- Vector: agreement text says "leverage ≤ 4.0x" → 0.2x headroom
- Graph: which covenant definition applies to which loan

## Chunking Strategy

- Chunk size: ~1000 tokens
- Overlap: 200 tokens (prevents context loss at chunk boundaries)
- Classification: each chunk tagged as `covenant`, `financial`, or `general`
- Why overlap? Covenant clauses often span multiple paragraphs

## Anti-Hallucination Design

1. Prompt: "Use ONLY the provided context. Do not add information not present."
2. Structured output: LLM returns JSON → validated before storage
3. Null for missing: "use null if not found" → never inferred
4. Citations: every Copilot response must cite its sources
