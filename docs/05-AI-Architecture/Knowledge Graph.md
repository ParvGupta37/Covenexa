# Knowledge Graph Architecture

## What is it?

Covenexa's Knowledge Graph connects entities across the private credit portfolio into a traversable relationship graph. Rather than querying isolated tables, the graph allows reasoning like: "Show me all covenants across all agreements for all active loans of this borrower."

---

## Graph Structure

```
Organization
    └── Borrower ──────────────────────────────────────────┐
          ├── Loan ──> Agreement ──> DocumentChunk          │
          │                └──> Covenant ──────────────────►│
          │                └──> FinancialMetric ────────────┘
          ├── BorrowerHealthScore
          ├── RiskAssessment
          └── Alert
```

---

## v1.0 Implementation (PostgreSQL → Graph API)

The Knowledge Graph API (`GET /api/v1/risk/graph/{borrower_id}`) builds the graph **in-memory from PostgreSQL** and returns it as a node-edge JSON object for the frontend to visualize.

```python
# Pseudocode: risk.py graph endpoint
nodes = [
    { id: borrower_id, type: "borrower", label: company_name },
    { id: loan_id, type: "loan", label: f"${amount}M" },
    { id: agreement_id, type: "agreement", label: filename },
    ...{ id: covenant.id, type: "covenant", label: covenant.name }
    ...{ id: metric.id, type: "financial_metric", label: period }
]
edges = [
    { source: borrower_id, target: loan_id, label: "HAS_LOAN" },
    { source: loan_id, target: agreement_id, label: "HAS_AGREEMENT" },
    ...
]
return { nodes, edges }
```

---

## v1.1 Target (Neo4j)

In v1.1, the DocumentWorkflow will write graph nodes and relationships to **Neo4j** on every pipeline run. The Graph Retriever will then query Neo4j using Cypher, enabling:

- Multi-hop traversal queries
- Cross-borrower relationship analysis
- Covenant-to-financial-metric linkage in the AI Copilot

**Neo4j** is already deployed and connected (`integrations/neo4j_client.py`). The write adapter and Cypher queries are the remaining work.

---

## Frontend Visualization (`/app/graph`)

The `GraphPage` renders the graph using a custom SVG-based force-directed layout:

- **Nodes** are colored by type (Borrower=blue, Loan=indigo, Agreement=purple, Covenant=orange, Metric=green)
- **Edges** show relationship labels on hover
- **Zoom + Pan** enabled
- **Click node** → shows entity detail panel

The raw data comes from `GET /api/v1/risk/graph/{borrower_id}`.