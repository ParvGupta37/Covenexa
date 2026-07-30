"""
Covenexa AI Workflows package.
Exposes WorkflowManager as the single entry gateway from backend routers.
"""
from ai.workflows.base_workflow import BaseWorkflow
from ai.workflows.document_workflow import DocumentWorkflow
from ai.workflows.compliance_workflow import ComplianceWorkflow
from ai.workflows.copilot_workflow import CopilotWorkflow
from ai.workflows.workflow_manager import WorkflowManager

__all__ = [
    "BaseWorkflow",
    "DocumentWorkflow",
    "ComplianceWorkflow",
    "CopilotWorkflow",
    "WorkflowManager",
]
