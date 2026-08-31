# Vector Database — Pinecone

## Purpose

Pinecone stores dense vector embeddings of document chunks from ingested loan agreements. It enables semantic similarity search — finding the most relevant agreement clauses for a given natural language query.

---

## Index Configuration

| Setting | Value |
|:--------|:------|
| Index Name | `covenexa-docs` |
| Embedding Model | Cohere Embed v4 (`embed-english-v3.0`) |
| Dimension | 1024 |
| Metric | Cosine similarity |
| Cloud | Pinecone managed (Serverless or Pod-based) |

---

## Namespace Strategy

Each document chunk is stored in a namespace keyed by `agreement_id`:

```
covenexa-docs
  └── namespace: {agreement_id_1}
        ├── vector: chunk-0 → embedding
        ├── vector: chunk-1 → embedding
        └── ...
  └── namespace: {agreement_id_2}
        └── ...
```

This provides **agreement-level isolation** without creating per-organization indexes.

---

## Metadata Schema

Each vector is stored with metadata for filtering:

```python
{
  "borrower_id": "uuid",
  "agreement_id": "uuid",
  "chunk_index": 0,
  "chunk_type": "covenant",  # or "financial", "general"
  "content_preview": "first 100 chars..."
}
```

---

## Query Pattern (Tenant-Isolated)

```python
# vector_retriever.py
results = pinecone_index.query(
    vector=embed(user_query),
    top_k=5,
    namespace=agreement_id,    # Namespace-level isolation
    filter={
        "borrower_id": {"$eq": borrower_id}  # Metadata filter
    },
    include_metadata=True
)
```

**Critical:** The filter is always applied. Zero results do NOT trigger an unfiltered retry.

---

## Write Pattern (DocumentAgent)

```python
# For each chunk after parsing:
embedding = cohere_client.embed(chunk.content)
pinecone_index.upsert(
    vectors=[(chunk.id, embedding, metadata)],
    namespace=agreement_id
)
```

---

## Integration Points

| Code File | Role |
|:----------|:-----|
| `integrations/pinecone_client.py` | Pinecone connection + index reference |
| `ai/rag/retrievers/vector_retriever.py` | Semantic search for RAG |
| `ai/agents/document_agent.py` | Chunk embedding + upsert on document ingestion |