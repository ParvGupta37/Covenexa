"""
Compliance Analysis Workflow (Unimplemented Scaffold).

STATUS: NOT IMPLEMENTED.
ComplianceWorkflow.execute() is a Sprint-3 planning scaffold.
WorkflowManager.trigger_compliance_run() exists but is NOT called by any
active API endpoint. Compliance evaluation is performed by CovenantMonitor
and RecommendationEngine inside RiskIntelligencePipeline.

DO NOT call this workflow in production paths until it is fully implemented.
"""
from typing import Any, Dict
import structlog
from ai.workflows.base_workflow import BaseWorkflow

logger = structlog.get_logger(__name__)


class ComplianceWorkflow(BaseWorkflow):
    """
    Unimplemented scaffold.
    Real compliance monitoring is in ai/engines/covenant_monitor.py.
    """

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # MEDIUM-2: Removed fabricated return values:
        #   "status": "compliance_checked_stub"
        #   "health_score": 85          <- invented business value
        #   "has_breach": False         <- invented compliance result
        # A dead-code stub must never emit fake business data.
        raise NotImplementedError(
            "ComplianceWorkflow is an unimplemented scaffold. "
            "Use RiskIntelligencePipeline / POST /api/v1/risk/pipeline/{borrower_id} instead."
        )
