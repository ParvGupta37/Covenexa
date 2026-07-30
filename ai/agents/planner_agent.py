"""
Planner Agent.
Acts as the central orchestrator.
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent
from ai.prompts.planner_prompt import PLANNER_SYSTEM_PROMPT, PlannerPrompt


class PlannerAgent(BaseAgent):
    """
    Decides execution workflows, assigns subtasks, and routes inputs.
    """

    @property
    def name(self) -> str:
        return "PlannerAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("user_query", "")
        # Process routing decisions
        prompt = PlannerPrompt().format(user_query=query, retrieved_context="[Stub Context]")
        response = await self._llm.generate_response(prompt, system_prompt=PLANNER_SYSTEM_PROMPT)
        
        state.update({
            "planner_output": response,
            "next_step": "document_parsing",
        })
        return state
