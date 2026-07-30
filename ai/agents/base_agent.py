"""
Abstract Base Agent class.
All multi-agent modules inherit from this base class.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from ai.llm.llm_service import LLMService


class BaseAgent(ABC):
    """
    Abstract Base Agent.
    Every agent interacts with the LLM via LLMService and receives tools via MCP Server.
    """

    def __init__(self, llm_service: LLMService, mcp_client: Any) -> None:
        self._llm = llm_service
        self._mcp = mcp_client

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the agent."""
        ...

    @abstractmethod
    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic based on the input workflow state.
        Returns the updated state keys dictionary.
        """
        ...
