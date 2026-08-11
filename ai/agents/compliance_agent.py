"""
Compliance Agent (Unimplemented Scaffold).

STATUS: NOT IMPLEMENTED.
This agent is a Sprint-3 planning scaffold. It is not called by any active API
path. Compliance monitoring is performed by CovenantMonitor
(ai/engines/covenant_monitor.py) and RecommendationEngine, both wired into
RiskIntelligencePipeline.

DO NOT remove this file — it is referenced in Sprint planning documents.
"""
from typing import Any, Dict
from ai.agents.base_agent import BaseAgent


class ComplianceAgent(BaseAgent):
    """
    Unimplemented placeholder.
    Real compliance evaluation is in ai/engines/covenant_monitor.py.
    """

    @property
    def name(self) -> str:
        return "ComplianceAgent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # MEDIUM-2: Removed "compliance_status: checked_stub" emit.
        # An unimplemented agent must never emit an invented compliance result.
        raise NotImplementedError(
            "ComplianceAgent is an unimplemented scaffold. "
            "Use CovenantMonitor / GET /api/v1/risk/covenants/{borrower_id} instead."
        )
