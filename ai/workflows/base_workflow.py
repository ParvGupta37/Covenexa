"""
Base workflow structure.
Sets up the common state format dictionary used by LangGraph nodes.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseWorkflow(ABC):
    """
    Abstract Base Workflow wrapping LangGraph executions.
    """

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs the workflow graph state machine.
        """
        ...
