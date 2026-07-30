"""
Copilot Agent (Stub).
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent
from ai.prompts.copilot_prompt import COPILOT_SYSTEM_PROMPT, CopilotPrompt


class CopilotAgent(BaseAgent):
    """
    RAG conversational answering agent.
    Fleshed out in Sprint 4.
    """

    @property
    def name(self) -> str:
        return "CopilotAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("user_query", "")
        # Build prompt using retrieved context
        prompt = CopilotPrompt().format(
            retrieved_context="[Retrieved Knowledge Base Context]",
            user_query=query,
        )
        response = await self._llm.generate_response(prompt, system_prompt=COPILOT_SYSTEM_PROMPT)
        
        state.update({"response": response})
        return state
