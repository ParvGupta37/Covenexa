"""
Neo4j knowledge graph retriever.
Queries structural relations between Borrowers, Loans, Agreements, and Covenants.
"""
from typing import Any, List
import structlog
from ai.rag.retrievers.base_retriever import BaseRetriever
from integrations.neo4j.client import Neo4jClient
from app.core.config import settings

logger = structlog.get_logger(__name__)


class GraphRetriever(BaseRetriever):
    """
    Traverses the Covenexa Neo4j Knowledge Graph to find linked covenants and borrowers.
    """

    def __init__(self, neo4j_client: Neo4jClient | None = None) -> None:
        self._client = neo4j_client or Neo4jClient(
            uri=settings.NEO4J_URI,
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
        )
        self._client.initialize()

    async def retrieve(self, query: str, limit: int = 5, **kwargs: Any) -> List[dict]:
        logger.info("graph.retrieve", query=query, limit=limit)
        
        borrower_id = kwargs.get("borrower_id")
        agreement_id = kwargs.get("agreement_id")

        try:
            if borrower_id:
                # Query all covenants linked to this borrower
                cypher = """
                MATCH (b:Borrower {id: $borrower_id})-[:HAS_COVENANT]->(c:Covenant)
                RETURN b.company_name as borrower_name, c.name as covenant_name, 
                       c.covenant_type as covenant_type, c.formula as formula, 
                       c.threshold as threshold
                LIMIT $limit
                """
                params = {"borrower_id": borrower_id, "limit": limit}
            elif agreement_id:
                # Query all covenants linked to this agreement
                cypher = """
                MATCH (a:Agreement {id: $agreement_id})-[:HAS_COVENANT]->(c:Covenant)
                RETURN a.id as agreement_id, c.name as covenant_name, 
                       c.covenant_type as covenant_type, c.formula as formula, 
                       c.threshold as threshold
                LIMIT $limit
                """
                params = {"agreement_id": agreement_id, "limit": limit}
            else:
                # General keyword lookup on covenant nodes
                cypher = """
                MATCH (c:Covenant)
                WHERE toLower(c.name) CONTAINS toLower($query) 
                   OR toLower(c.formula) CONTAINS toLower($query)
                RETURN c.name as covenant_name, c.covenant_type as covenant_type, 
                       c.formula as formula, c.threshold as threshold
                LIMIT $limit
                """
                params = {"query": query, "limit": limit}

            records = await self._client.execute_query(cypher, params)
            
            results = []
            for rec in records:
                results.append({
                    "source": "knowledge_graph",
                    "content": f"Covenant: {rec.get('covenant_name')} ({rec.get('covenant_type')}) "
                               f"| Formula: {rec.get('formula', 'N/A')} "
                               f"| Threshold: {rec.get('threshold', 'N/A')}",
                    "score": 0.9,
                    "metadata": rec,
                })
            return results
        except Exception as exc:
            logger.warning("graph.retrieve_failed", error=str(exc))
            # Gracefully fail returning empty list in local dev if Neo4j is down
            return []
