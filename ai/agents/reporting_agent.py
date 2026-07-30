"""
Reporting Agent (Stub).
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent


class ReportingAgent(BaseAgent):
    """
    Fleshed out in Sprint 4 with report compilation templates.
    """

    @property
    def name(self) -> str:
        return "ReportingAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update({"report_markdown": "# Summary\nGenerated report stub."})
        return state
