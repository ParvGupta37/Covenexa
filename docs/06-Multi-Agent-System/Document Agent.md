# Document Agent

## Purpose

Transform raw uploaded documents (PDF, DOCX, HTML) into structured, searchable knowledge: text chunks stored in PostgreSQL and vector embeddings stored in Pinecone.

---

## File

`ai/agents/document_agent.py`

---

## Position in Pipeline

```
File Upload / SEC URL
       ↓
DocumentAgent     ← [This Agent]
       ↓
CovenantAgent
       ↓
FinancialAgent
```

---

## Inputs

- `agreement_id` — UUID of the uploaded agreement
- `file_path` — local filesystem path to the document
- `file_type` — `pdf`, `docx`, or `html`
- `borrower_id` — owner borrower UUID

---

## Processing Steps

### 1. Parse
- **PDF/DOCX:** LlamaIndex `SimpleDirectoryReader` → extracts raw text
- **HTML (SEC filings):** BeautifulSoup → strips HTML tags → extracts text content

### 2. Chunk
- Split into chunks of ~1000 tokens with 200-token overlap
- Each chunk assigned a `chunk_index` (position in document)
- Chunk type classified: `covenant`, `financial`, or `general`

### 3. Embed
- Each chunk passed to Cohere Embed v4 (`embed-english-v3.0`)
- Returns 1024-dimension dense vector

### 4. Upsert to Pinecone
- Vector stored in Pinecone namespace = `agreement_id`
- Metadata: `{ borrower_id, agreement_id, chunk_index, chunk_type }`
- `embedding_id` stored in PostgreSQL for traceability

### 5. Save to PostgreSQL
- INSERT `document_chunks` rows for each chunk
- UPDATE `agreements.parsing_status` → `"completed"`
- UPDATE `agreements.is_analyzed` → `True`

---

## Outputs

- `document_chunks` rows in PostgreSQL
- Vectors in Pinecone (namespace = agreement_id)
- Updated `agreements.parsing_status` and `is_analyzed`
- State passed to `CovenantAgent` in LangGraph workflow