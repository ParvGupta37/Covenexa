"""
PostgreSQL MCP Tool.
Exposes safe, parameterized read/write access to PostgreSQL for AI agents.
Agents must NEVER import SQLAlchemy directly — use this tool.
"""
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from mcp_server.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class PostgresTool(BaseTool):
    """
    MCP Tool: Provides parameterized SQL query execution for AI agents.

    Supported operations:
      - execute_read: SELECT queries (returns list of row dicts)
      - execute_write: INSERT / UPDATE / DELETE (returns affected rows)
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @property
    def name(self) -> str:
        return "postgres"

    @property
    def description(self) -> str:
        return (
            "Execute SQL queries against the Covenexa PostgreSQL database. "
            "Use 'execute_read' for SELECT and 'execute_write' for INSERT/UPDATE/DELETE. "
            "Always use parameterized queries — never interpolate user data into SQL."
        )

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Route to the appropriate operation based on 'operation' kwarg.

        Args:
            operation: 'execute_read' | 'execute_write'
            query: Parameterized SQL string
            params: dict of query parameters
        """
        operation = kwargs.get("operation", "execute_read")
        query = kwargs.get("query", "")
        params = kwargs.get("params", {})

        if not query:
            return {"success": False, "data": None, "error": "Query cannot be empty."}

        try:
            if operation == "execute_read":
                return await self._execute_read(query, params)
            elif operation == "execute_write":
                return await self._execute_write(query, params)
            else:
                return {"success": False, "data": None, "error": f"Unknown operation: {operation}"}
        except Exception as exc:
            logger.error("PostgresTool error [op=%s]: %s", operation, exc)
            return {"success": False, "data": None, "error": str(exc)}

    async def _execute_read(
        self,
        query: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a SELECT query and return rows as list of dicts."""
        result = await self._session.execute(text(query), params)
        rows = result.mappings().all()
        return {
            "success": True,
            "data": [dict(row) for row in rows],
            "error": None,
        }

    async def _execute_write(
        self,
        query: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute an INSERT/UPDATE/DELETE and return rowcount."""
        result = await self._session.execute(text(query), params)
        await self._session.commit()
        return {
            "success": True,
            "data": {"rows_affected": result.rowcount},
            "error": None,
        }
