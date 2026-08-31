# Neo4j Schema — Knowledge Graph

## Purpose

Neo4j stores the entity relationship graph for Covenexa's portfolio — connecting Borrowers, Loans, Agreements, Covenants, and Financial Metrics as a traversable graph. Enables relationship-based reasoning in the AI Copilot.

---

## Node Types

| Label | Properties |
|:------|:----------|
| `Borrower` | `id`, `company_name`, `sector`, `country`, `risk_level` |
| `Loan` | `id`, `principal_amount`, `interest_rate`, `maturity_date`, `status` |
| `Agreement` | `id`, `file_name`, `upload_date`, `parsing_status` |
| `Covenant` | `id`, `name`, `metric`, `threshold`, `operator` |
| `FinancialMetric` | `id`, `reporting_period`, `ebitda`, `debt_to_ebitda`, `interest_coverage` |

---

## Relationship Types

| Relationship | From → To | Meaning |
|:-------------|:----------|:--------|
| `HAS_LOAN` | Borrower → Loan | Borrower has an active facility |
| `HAS_AGREEMENT` | Loan → Agreement | Loan is governed by an agreement |
| `HAS_COVENANT` | Agreement → Covenant | Agreement defines a covenant |
| `APPLIES_TO` | Covenant → Borrower | Covenant monitors this borrower |
| `HAS_METRICS` | Borrower → FinancialMetric | Borrower has a financial reporting period |

---

## v1.0 Status

> **Note:** Neo4j is connected on startup (`integrations/neo4j_client.py`) but the Knowledge Graph nodes are **not yet written** from the pipeline. The Knowledge Graph page (`/app/graph`) serves graph data from PostgreSQL, transformed into a node-edge format in memory.

Activating Neo4j for real graph traversal is planned for v1.1.

---

## Graph Traversal Example (Planned)

```cypher
// Find all covenants for a borrower
MATCH (b:Borrower {id: $borrower_id})-[:HAS_LOAN]->(l:Loan)-[:HAS_AGREEMENT]->(a:Agreement)-[:HAS_COVENANT]->(c:Covenant)
RETURN b.company_name, l.id, c.name, c.threshold, c.metric

// Find all borrowers with leverage covenant breach risk
MATCH (b:Borrower)-[:HAS_METRICS]->(m:FinancialMetric)
WHERE m.debt_to_ebitda > 3.5
RETURN b.company_name, m.debt_to_ebitda
ORDER BY m.debt_to_ebitda DESC
```