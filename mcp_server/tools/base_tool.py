"""
Abstract base class for all MCP tools.

Every tool in the MCP Server must inherit from BaseTool.
This ensures a consistent interface for the tool registry
and enables future dynamic tool discovery.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """
    Abstract base for all MCP tools.

    Subclasses define:
      - name: unique tool identifier used by agents
      - description: shown to the Planner Agent for tool selection
      - execute(): performs the actual operation
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name (e.g., 'query_postgres')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description for the Planner Agent."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the tool operation.

        Returns:
            A dict with at minimum:
              - 'success': bool
              - 'data': Any (result payload)
              - 'error': str | None
        """
        ...

    def as_schema(self) -> dict[str, Any]:
        """Return the tool's metadata schema for registration."""
        return {
            "name": self.name,
            "description": self.description,
            "tool_class": self.__class__.__name__,
        }
