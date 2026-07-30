"""
Workflow Manager.
This is the ONLY entry point the Backend API uses to invoke multi-agent pipelines.
"""
from typing import Any, Dict
import structlog

from ai.workflows.document_workflow import DocumentWorkflow
from ai.workflows.compliance_workflow import ComplianceWorkflow
from ai.workflows.copilot_workflow import CopilotWorkflow

logger = structlog.get_logger(__name__)


class WorkflowManager:
    """
    Decouples Backend APIs from multi-agent configurations.
    Routes execution requests to the correct LangGraph workflow handler.
    """

    def __init__(self) -> None:
        self._doc_workflow = DocumentWorkflow()
        self._compliance_workflow = ComplianceWorkflow()
        self._copilot_workflow = CopilotWorkflow()

    async def trigger_document_ingestion(self, agreement_id: str, file_path: str, file_type: str) -> Dict[str, Any]:
        """Runs the parsing, covenant extraction, and vector index update graph."""
        logger.info("workflow_manager.document_ingestion", agreement_id=agreement_id)
        return await self._doc_workflow.execute({
            "agreement_id": agreement_id,
            "file_path": file_path,
            "file_type": file_type,
        })

    async def trigger_compliance_run(self, borrower_id: str, statement_id: str) -> Dict[str, Any]:
        """Runs the financial parsing, headroom calculations, and score evaluations."""
        logger.info("workflow_manager.compliance_run", borrower_id=borrower_id)
        return await self._compliance_workflow.execute({
            "borrower_id": borrower_id,
            "statement_id": statement_id,
        })

    async def trigger_copilot_query(self, session_id: str, query: str) -> Dict[str, Any]:
        """Runs intent checks, hybrid GraphRAG context retrieval, and conversation response."""
        logger.info("workflow_manager.copilot_query", session_id=session_id)
        return await self._copilot_workflow.execute({
            "session_id": session_id,
            "user_query": query,
        })
