"""
Handler for DocumentUploadedEvent.
Subscribes to Event Bus, triggers multi-agent ingestion workflow.
"""
import asyncio
from typing import Any
import structlog

from event_bus.handlers.base_handler import BaseHandler
from ai.workflows.workflow_manager import WorkflowManager

logger = structlog.get_logger(__name__)


_tasks: set[asyncio.Task] = set()


class DocumentUploadedHandler(BaseHandler):
    """
    Listens to DocumentUploadedEvent on the Event Bus,
    extracts the metadata, and invokes WorkflowManager.
    """

    def __init__(self) -> None:
        self._manager = WorkflowManager()

    async def handle(self, event_data: dict[str, Any]) -> None:
        logger.info("event_handler.document_uploaded.start", event_id=event_data.get("event_id"))
        
        agreement_id = event_data.get("agreement_id")
        file_path = event_data.get("file_path")
        file_type = event_data.get("file_type", "loan_agreement")

        if not agreement_id or not file_path:
            logger.error("event_handler.document_uploaded.missing_fields", data=event_data)
            return

        # Trigger ingestion asynchronously with a strong reference to prevent GC
        task = asyncio.create_task(self._run_workflow(agreement_id, file_path, file_type))
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)

    async def _run_workflow(self, agreement_id: str, file_path: str, file_type: str) -> None:
        try:
            result = await self._manager.trigger_document_ingestion(
                agreement_id=agreement_id,
                file_path=file_path,
                file_type=file_type,
            )
            logger.info("event_handler.document_uploaded.success", agreement_id=agreement_id, status=result.get("status"))
        except Exception as exc:
            logger.error("event_handler.document_uploaded.failed", agreement_id=agreement_id, error=str(exc))
