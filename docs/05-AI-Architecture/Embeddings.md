# Embeddings — Cohere Embed v4

## Model

**Cohere Embed v4** (`embed-english-v3.0`)

- Dimension: **1024**
- Metric: Cosine similarity
- Language: English (optimized for financial and legal text)
- Provider: Cohere API

---

## Usage in Covenexa

### Document Chunk Embedding (Write Path)

When a document is uploaded and processed by `DocumentAgent`:

```python
# integrations/cohere_client.py
embeddings = cohere_client.embed(
    texts=[chunk.content for chunk in chunks],
    model="embed-english-v3.0",
    input_type="search_document"  # For indexing
)
```

Each chunk's embedding is upserted to Pinecone with `input_type="search_document"`.

### Query Embedding (Read Path)

When the Copilot receives a user query:

```python
query_embedding = cohere_client.embed(
    texts=[user_query],
    model="embed-english-v3.0",
    input_type="search_query"  # For querying
)
```

`input_type="search_query"` produces embeddings optimized for retrieval (asymmetric search).

---

## Why Cohere Embed v4?

| Criterion | Choice |
|:----------|:-------|
| Legal/financial domain | Cohere v4 performs well on long-form legal document chunking |
| Dimension (1024) | Higher than typical 768-dim models — better semantic granularity |
| Asymmetric support | `search_document` vs. `search_query` input types improve retrieval quality |
| API stability | Cohere provides a stable managed API with predictable pricing |

---

## Configuration Consistency

The embedding model is configured once in `app/core/config.py`:

```python
COHERE_EMBED_MODEL: str = "embed-english-v3.0"
```

Both the `CohereClient` (for generating embeddings) and the `VectorRetriever` (for querying) use this shared config. A production test validates this consistency:

```
test_cohere_embed_model_config_is_consistent ✅
```

---

## Without API Key

If `COHERE_API_KEY` is not set, embedding calls return a mock vector (1024-dim zero vector with a small random perturbation). This allows the pipeline to complete without Pinecone upsert failures. Logged as `[MOCK EMBEDDING]`.