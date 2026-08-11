"""
Planner Agent (Unimplemented Scaffold).

STATUS: NOT IMPLEMENTED.
This agent was intended to orchestrate multi-agent workflows by routing
user queries. The active AI Copilot uses CopilotAgent + RetrieverFactory
(Hybrid GraphRAG) instead — see ai/agents/copilot_agent.py.

DO NOT remove this file — it is referenced in Sprint planning documents.
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """
    Unimplemented placeholder.
    Active query routing is in ai/agents/copilot_agent.py + RetrieverFactory.
    """

    @property
    def name(self) -> str:
        return "PlannerAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # MEDIUM-2: Removed hardcoded "[Stub Context]" RAG placeholder.
        # This agent is not wired into any active pipeline; CopilotAgent
        # uses RetrieverFactory (SQL + Pinecone + Neo4j) for real context.
        raise NotImplementedError(
            "PlannerAgent is an unimplemented scaffold. "
            "The active Copilot pipeline uses CopilotAgent + RetrieverFactory instead."
        )
