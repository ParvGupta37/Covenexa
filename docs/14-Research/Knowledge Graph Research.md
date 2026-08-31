# Knowledge Graph Research Notes

## Why a Knowledge Graph for Private Credit?

Traditional SQL databases excel at querying structured data in isolation. But private credit portfolios have **rich relational structure**:

- A Borrower has multiple Loans
- Each Loan has multiple Agreements (versions)
- Each Agreement contains multiple Covenants
- Each Covenant references a financial metric
- Multiple Covenants may share the same metric but have different thresholds per facility

SQL JOINs can answer some of these questions, but as the graph gets deeper and more complex, Cypher (Neo4j's query language) becomes significantly more expressive.

## Graph Database vs. Relational Database

| Query Type | SQL | Neo4j (Cypher) |
|:-----------|:----|:--------------|
| "List all covenants for borrower X" | 3-table JOIN | 1 MATCH traversal |
| "Find borrowers sharing a legal counsel" | Complex JOIN | Direct MATCH |
| "Which covenants are close to breach AND their facility matures in <6 months?" | Multi-table JOIN + subquery | Pattern match + filter |

## Neo4j in Covenexa

**v1.0:** Neo4j is connected but the knowledge graph is built in-memory from PostgreSQL and served as nodes/edges to the frontend.

**v1.1 plan:** Write agent populates Neo4j on every pipeline run. Graph retriever queries Neo4j via `neo4j-driver`. Cypher queries power the GraphRAG context.

## Key Cypher Patterns

```cypher
// All covenants close to breach for a borrower
MATCH (b:Borrower {id: $borrower_id})-[:HAS_LOAN]->(l:Loan)
      -[:HAS_AGREEMENT]->(a:Agreement)-[:HAS_COVENANT]->(c:Covenant)
MATCH (c)-[:MONITORED_BY]->(m:CovenantMonitoring)
WHERE m.headroom < 0.15
RETURN b.company_name, c.name, m.headroom, m.status
ORDER BY m.headroom ASC
```
