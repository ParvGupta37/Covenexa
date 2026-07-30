"""
Recommendation Agent (Stub).
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent


class RecommendationAgent(BaseAgent):
    """
    Fleshed out in Sprint 3 with credit review guidelines actions suggestions.
    """

    @property
    def name(self) -> str:
        return "RecommendationAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        state.update({"recommendations": []})
        return state
