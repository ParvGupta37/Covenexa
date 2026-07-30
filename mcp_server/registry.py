"""
MCP Server Tool Registry.
Manages registration and discovery of all MCP tools.
New tools can be added without modifying the server — just register them here.
"""
import logging
from typing import Any

from mcp_server.tools.base_tool import BaseTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Central registry for all MCP tools.

    Tools are registered by name. The Planner Agent queries
    the registry to discover what tools are available and
    selects the appropriate tool for each sub-task.
    """

    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool instance.

        Args:
            tool: A BaseTool subclass instance.

        Raises:
            ValueError: If a tool with the same name is already registered.
        """
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' is already registered. "
                "Use a unique name or deregister the existing tool first."
            )
        self._tools[tool.name] = tool
        logger.info("MCP tool registered: '%s'", tool.name)

    def deregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.info("MCP tool deregistered: '%s'", tool_name)

    def get(self, tool_name: str) -> BaseTool:
        """
        Retrieve a tool by name.

        Raises:
            KeyError: If the tool is not registered.
        """
        if tool_name not in self._tools:
            raise KeyError(
                f"MCP tool '{tool_name}' is not registered. "
                f"Available tools: {list(self._tools.keys())}"
            )
        return self._tools[tool_name]

    async def execute(self, tool_name: str, **kwargs: Any) -> dict[str, Any]:
        """
        Convenience method: look up and execute a tool in one call.

        Args:
            tool_name: Registered tool name.
            **kwargs: Arguments forwarded to tool.execute().

        Returns:
            Tool execution result dict.
        """
        try:
            tool = self.get(tool_name)
            logger.debug("Executing MCP tool '%s' with kwargs: %s", tool_name, kwargs)
            result = await tool.execute(**kwargs)
            return result
        except KeyError as exc:
            logger.error("Tool not found: %s", exc)
            return {"success": False, "data": None, "error": str(exc)}
        except Exception as exc:
            logger.error("Tool execution error [tool=%s]: %s", tool_name, exc)
            return {"success": False, "data": None, "error": str(exc)}

    def list_tools(self) -> list[dict[str, str]]:
        """Return schemas of all registered tools (for agent introspection)."""
        return [tool.as_schema() for tool in self._tools.values()]

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        return tool_name in self._tools
