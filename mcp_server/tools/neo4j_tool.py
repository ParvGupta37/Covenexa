"""
Neo4j MCP Tool.
Exposes Cypher query execution and graph mutation for AI agents.
Agents must NEVER import the Neo4j driver directly — use this tool.
"""
import logging
from typing import Any

from mcp_server.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class Neo4jTool(BaseTool):
    """
    MCP Tool: Knowledge Graph access via Neo4j Cypher.

    Supported operations:
      - query_graph: Read-only Cypher (MATCH, RETURN)
      - upsert_node: Create or update a node
      - upsert_relation: Create or update a relationship
      - delete_node: Delete a node by id
    """

    def __init__(self, neo4j_client: Any) -> None:
        self._client = neo4j_client

    @property
    def name(self) -> str:
        return "neo4j"

    @property
    def description(self) -> str:
        return (
            "Execute Cypher queries against the Covenexa Knowledge Graph in Neo4j. "
            "Use 'query_graph' for reads, 'upsert_node'/'upsert_relation' for writes. "
            "The graph connects Borrowers, Loans, Agreements, Covenants, and Financial Metrics."
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Route to the appropriate graph operation.

        Args:
            operation: 'query_graph' | 'upsert_node' | 'upsert_relation' | 'delete_node'
            cypher: Cypher query string (for query_graph)
            params: Cypher parameters dict
            label: Node label (for upsert_node)
            properties: Node properties (for upsert_node)
            match_key: Property key used for MERGE (for upsert_node)
            from_id: Source node id (for upsert_relation)
            to_id: Target node id (for upsert_relation)
            relation_type: Relationship type (for upsert_relation)
        """
        operation = kwargs.get("operation", "query_graph")

        try:
            if operation == "query_graph":
                return await self._query_graph(
                    kwargs.get("cypher", ""),
                    kwargs.get("params", {}),
                )
            elif operation == "upsert_node":
                return await self._upsert_node(
                    kwargs.get("label", ""),
                    kwargs.get("properties", {}),
                    kwargs.get("match_key", "id"),
                )
            elif operation == "upsert_relation":
                return await self._upsert_relation(
                    kwargs.get("from_id"),
                    kwargs.get("to_id"),
                    kwargs.get("relation_type", "RELATES_TO"),
                    kwargs.get("from_label", "Node"),
                    kwargs.get("to_label", "Node"),
                    kwargs.get("properties", {}),
                )
            elif operation == "delete_node":
                return await self._delete_node(
                    kwargs.get("label", ""),
                    kwargs.get("node_id"),
                )
            else:
                return {"success": False, "data": None, "error": f"Unknown operation: {operation}"}
        except Exception as exc:
            logger.error("Neo4jTool error [op=%s]: %s", operation, exc)
            return {"success": False, "data": None, "error": str(exc)}

    async def _query_graph(
        self,
        cypher: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a read Cypher query."""
        if not cypher:
            return {"success": False, "data": None, "error": "Cypher query cannot be empty."}
        records = await self._client.execute_query(cypher, params)
        return {"success": True, "data": records, "error": None}

    async def _upsert_node(
        self,
        label: str,
        properties: dict[str, Any],
        match_key: str,
    ) -> dict[str, Any]:
        """MERGE a node in the graph, creating or updating it."""
        match_value = properties.get(match_key)
        if not match_value:
            return {"success": False, "data": None, "error": f"Match key '{match_key}' not found in properties."}

        cypher = (
            f"MERGE (n:{label} {{{match_key}: $match_value}}) "
            "SET n += $properties "
            "RETURN n"
        )
        records = await self._client.execute_query(
            cypher,
            {"match_value": match_value, "properties": properties},
        )
        return {"success": True, "data": records, "error": None}

    async def _upsert_relation(
        self,
        from_id: Any,
        to_id: Any,
        relation_type: str,
        from_label: str,
        to_label: str,
        properties: dict[str, Any],
    ) -> dict[str, Any]:
        """MERGE a relationship between two nodes."""
        cypher = (
            f"MATCH (a:{from_label} {{id: $from_id}}) "
            f"MATCH (b:{to_label} {{id: $to_id}}) "
            f"MERGE (a)-[r:{relation_type}]->(b) "
            "SET r += $properties "
            "RETURN r"
        )
        records = await self._client.execute_query(
            cypher,
            {"from_id": from_id, "to_id": to_id, "properties": properties},
        )
        return {"success": True, "data": records, "error": None}

    async def _delete_node(
        self,
        label: str,
        node_id: Any,
    ) -> dict[str, Any]:
        """Detach and delete a node."""
        cypher = f"MATCH (n:{label} {{id: $id}}) DETACH DELETE n"
        await self._client.execute_query(cypher, {"id": node_id})
        return {"success": True, "data": {"deleted": True}, "error": None}
