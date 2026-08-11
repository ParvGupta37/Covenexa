"""
Portfolio Agent (Unimplemented Scaffold).

STATUS: NOT IMPLEMENTED.
This agent is a Sprint-3 planning scaffold. It is not called by any active API
path. The actual health-score calculation is performed by HealthScoreEngine
(ai/engines/health_score_engine.py), which is wired into RiskIntelligencePipeline.

DO NOT use this agent to retrieve portfolio health data; use the
  GET /api/v1/risk/health/{borrower_id}  endpoint instead.

DO NOT remove this file — it is referenced in Sprint planning documents.
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent


class PortfolioAgent(BaseAgent):
    """
    Unimplemented placeholder.
    Real portfolio health scoring is in ai/engines/health_score_engine.py.
    """

    @property
    def name(self) -> str:
        return "PortfolioAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # MEDIUM-2: Removed hardcoded portfolio_health_score = 85.
        # An unimplemented agent must never emit an invented business value.
        raise NotImplementedError(
            "PortfolioAgent is an unimplemented scaffold. "
            "Use HealthScoreEngine / GET /api/v1/risk/health/{borrower_id} instead."
        )
