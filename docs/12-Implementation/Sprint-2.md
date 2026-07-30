# Sprint 2 — Intelligent Document Processing & Hybrid GraphRAG

## Sprint Goal

Enable Covenexa to transform uploaded loan agreements and financial statements into structured knowledge that powers AI-driven covenant monitoring.

At the end of Sprint 2, a user should be able to upload a document and see extracted covenants, financial metrics, and searchable knowledge on the dashboard.

---

# Objectives

- Build the complete document ingestion pipeline.
- Parse and structure documents.
- Generate semantic embeddings.
- Build the Knowledge Graph.
- Extract covenant clauses.
- Parse financial statements.
- Implement Hybrid GraphRAG.
- Display extracted information on the dashboard.

---

# Features

## 1. Document Upload

Support:

- PDF
- DOCX
- XLSX
- CSV

Each upload creates a Document record with:

- Borrower
- Document Type
- Upload Time
- Processing Status

---

## 2. OCR & Parsing

Use:

- LlamaParse
- OCR fallback

Extract:

- Text
- Tables
- Page Numbers
- Section Hierarchy

---

## 3. Semantic Chunking

Split documents into meaningful chunks.

Each chunk stores:

- Chunk ID
- Page
- Section
- Content
- Metadata

---

## 4. Cohere Embeddings

Generate embeddings using Cohere Embed v4.

Store vectors in Pinecone.

Metadata includes:

- Borrower
- Document
- Page
- Section
- Document Type

---

## 5. Knowledge Graph

Store entities in Neo4j.

Nodes:

- Borrower
- Loan
- Agreement
- Covenant
- Financial Metric
- Amendment

Relationships:

- HAS_LOAN
- HAS_COVENANT
- AMENDS
- REFERENCES
- REPORTS

---

## 6. Covenant Extraction Agent

Extract:

- Covenant Name
- Formula
- Threshold
- Frequency
- Cure Period
- Event of Default
- Amendment References

Persist results in PostgreSQL and Neo4j.

---

## 7. Financial Statement Parser

Extract:

- Revenue
- EBITDA
- Net Income
- Total Debt
- Cash
- Interest Expense
- Leverage Ratio inputs
- Interest Coverage inputs

Store structured financial metrics in PostgreSQL.

---

## 8. Hybrid GraphRAG

Implement retrieval using:

- Pinecone (semantic search)
- Neo4j (relationship search)
- PostgreSQL (structured metadata)

Retrieval Flow:

User Query

↓

Planner

↓

Hybrid Retriever

↓

Vector Search

↓

Graph Search

↓

SQL Lookup

↓

Context Builder

↓

LLM

---

## 9. Event-Driven Processing

Workflow:

Document Uploaded

↓

Document Parsed

↓

Chunks Created

↓

Embeddings Generated

↓

Knowledge Graph Updated

↓

Financial Metrics Extracted

↓

Covenants Extracted

↓

Dashboard Updated

Each step publishes events through Redis Pub/Sub.

---

## 10. MCP Integration

All agents interact with infrastructure through the MCP Server.

Available tools:

- Read File
- Write PostgreSQL
- Read PostgreSQL
- Read Neo4j
- Write Neo4j
- Store Embeddings
- Retrieve Embeddings

---

## 11. Dashboard Integration

Display:

- Uploaded Documents
- Processing Status
- Extracted Covenants
- Financial Metrics
- Knowledge Graph Statistics
- Processing Timeline
- AI Extraction Logs

---

# Out of Scope

Do NOT implement:

- Borrower Health Score
- Default Prediction
- Portfolio Stress Testing
- AI Recommendations
- AI Copilot

These belong to Sprint 3 and Sprint 4.

---

# Definition of Done

Sprint 2 is complete when:

✓ Documents upload successfully.

✓ OCR and parsing complete.

✓ Semantic chunks created.

✓ Embeddings stored in Pinecone.

✓ Knowledge Graph populated.

✓ Financial metrics extracted.

✓ Covenants extracted.

✓ PostgreSQL updated.

✓ Hybrid GraphRAG operational.

✓ Dashboard displays extracted information.