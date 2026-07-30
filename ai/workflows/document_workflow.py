"""
Document Ingestion Workflow.
Uses LangGraph to sequence DocumentAgent -> CovenantAgent -> FinancialAgent.
"""
from typing import Any, Dict, List, Optional, TypedDict
import os
import structlog
from langgraph.graph import StateGraph, START, END

from ai.workflows.base_workflow import BaseWorkflow
from ai.llm.llm_service import LLMService
from ai.llm.cohere_provider import CohereProvider
from ai.mcp_client import MCPClient

from ai.agents.document_agent import DocumentAgent
from ai.agents.covenant_agent import CovenantAgent
from ai.agents.financial_agent import FinancialAgent

logger = structlog.get_logger(__name__)


class DocumentState(TypedDict):
    agreement_id: str
    borrower_id: str
    file_path: str
    file_type: str
    parsed_text: str
    page_count: int
    chunk_count: int
    extracted_covenants: List[dict]
    extracted_metrics: dict
    status: str
    error: Optional[str]


class DocumentWorkflow(BaseWorkflow):
    """
    Orchestrates the multi-agent pipeline for document ingestion.
    START → DocumentAgent → CovenantAgent → FinancialAgent → END
    """

    def __init__(self) -> None:
        # Initialize dependencies
        cohere_key = os.getenv("COHERE_API_KEY", "not_set")
        provider = CohereProvider(api_key=cohere_key)
        self._llm = LLMService(provider)
        self._mcp = MCPClient()

        # Instantiate agents
        self._doc_agent = DocumentAgent(self._llm, self._mcp)
        self._cov_agent = CovenantAgent(self._llm, self._mcp)
        self._fin_agent = FinancialAgent(self._llm, self._mcp)

        # Build LangGraph StateGraph
        builder = StateGraph(DocumentState)

        # Add Nodes
        builder.add_node("document_agent", self._doc_node)
        builder.add_node("covenant_agent", self._cov_node)
        builder.add_node("financial_agent", self._fin_node)

        # Add Edges
        builder.add_edge(START, "document_agent")
        builder.add_conditional_edges(
            "document_agent",
            self._route_after_document,
            {
                "continue": "covenant_agent",
                "fail": END,
            }
        )
        builder.add_conditional_edges(
            "covenant_agent",
            self._route_after_covenant,
            {
                "continue": "financial_agent",
                "fail": END,
            }
        )
        builder.add_edge("financial_agent", END)

        self._graph = builder.compile()
        logger.info("document_workflow.graph_compiled")

    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the compiled LangGraph workflow state machine."""
        agreement_id = inputs.get("agreement_id", "")
        logger.info("document_workflow.execute_start", agreement_id=agreement_id)
        
        # Query borrower_id via postgres MCP tool
        borrower_id = ""
        try:
            res = await self._mcp.execute_tool(
                tool_name="postgres",
                operation="execute_read",
                params={
                    "query": """
                        SELECT l.borrower_id 
                        FROM loans l 
                        JOIN agreements a ON a.loan_id = l.id 
                        WHERE a.id = :agreement_id
                    """,
                    "params": {"agreement_id": agreement_id}
                }
            )
            if res.get("success") and res.get("data"):
                borrower_id = res["data"][0].get("borrower_id", "")
        except Exception as exc:
            logger.error("document_workflow.get_borrower_failed", error=str(exc))

        # Initialize state dict
        initial_state: DocumentState = {
            "agreement_id": agreement_id,
            "borrower_id": borrower_id,
            "file_path": inputs.get("file_path", ""),
            "file_type": inputs.get("file_type", "loan_agreement"),
            "parsed_text": "",
            "page_count": 0,
            "chunk_count": 0,
            "extracted_covenants": [],
            "extracted_metrics": {},
            "status": "pending",
            "error": None,
        }

        # Run StateGraph
        final_state = await self._graph.ainvoke(initial_state)
        logger.info("document_workflow.execute_complete", status=final_state.get("status"))
        return final_state

    # ── NODE RUNNERS ────────────────────────────────────────────────
    async def _doc_node(self, state: DocumentState) -> DocumentState:
        return await self._doc_agent.run(state)

    async def _cov_node(self, state: DocumentState) -> DocumentState:
        return await self._cov_agent.run(state)

    async def _fin_node(self, state: DocumentState) -> DocumentState:
        return await self._fin_agent.run(state)

    # ── ROUTING LOGIC ───────────────────────────────────────────────
    def _route_after_document(self, state: DocumentState) -> str:
        if state.get("status") == "failed":
            return "fail"
        return "continue"

    def _route_after_covenant(self, state: DocumentState) -> str:
        if state.get("status") == "failed":
            return "fail"
        return "continue"
