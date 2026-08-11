"""
Neo4j knowledge graph retriever.
Queries structural relations between Borrowers, Loans/Facilities, Agreements, Covenants, and Risk.
"""
from typing import Any, List
import structlog
from ai.rag.retrievers.base_retriever import BaseRetriever
from integrations.neo4j.client import Neo4jClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class GraphRetriever(BaseRetriever):
    """
    Traverses the Covenexa Neo4j Knowledge Graph to find linked borrowers,
    facilities, covenants, and risk relationships.
    """

    def __init__(self, neo4j_client: Neo4jClient | None = None) -> None:
        self._client = neo4j_client or Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("graph.retrieve", query=query, limit=limit)
        borrower_id = kwargs.get("borrower_id")

        try:
            self._client.initialize()

            if borrower_id:
                # Relationship path: Borrower -> Loan/Facility -> Agreement -> Covenant
                cypher = """
                MATCH (b:Borrower {id: $borrower_id})
                OPTIONAL MATCH (b)-[:HAS_FACILITY|HAS_LOAN]->(l)
                OPTIONAL MATCH (b)-[:HAS_COVENANT]->(c:Covenant)
                OPTIONAL MATCH (l)-[:HAS_COVENANT]->(c2:Covenant)
                WITH b, COALESCE(c, c2) as cov, l
                WHERE cov IS NOT NULL
                RETURN b.company_name as borrower_name,
                       l.facility_name as facility_name,
                       cov.name as covenant_name,
                       cov.covenant_type as covenant_type,
                       cov.threshold as threshold
                LIMIT $limit
                """
                params = {"borrower_id": borrower_id, "limit": limit}
            else:
                # Keyword search on covenant nodes
                cypher = """
                MATCH (c:Covenant)
                WHERE toLower(c.name) CONTAINS toLower($query)
                RETURN c.name as covenant_name, c.covenant_type as covenant_type,
                       c.threshold as threshold
                LIMIT $limit
                """
                params = {"query": query, "limit": limit}

            records = await self._client.execute_query(cypher, params)

            results = []
            for rec in records:
                b_name = rec.get("borrower_name") or "Borrower"
                fac_name = rec.get("facility_name") or "Credit Facility"
                cov_name = rec.get("covenant_name") or "Covenant"
                cov_type = rec.get("covenant_type") or "maintenance"
                thresh = rec.get("threshold", "N/A")

                results.append({
                    "source": "neo4j_graph",
                    "content": f"[Graph Path: {b_name} ──► {fac_name} ──► Covenant '{cov_name}' ({cov_type}) | Threshold: {thresh}]",
                    "score": 0.90,
                    "metadata": rec,
                })
            return results
        except Exception as exc:
            logger.warning("graph.retrieve_failed", error=str(exc))
            return []
