"""
AI Copilot Endpoint — Sprint 3.
Provides Q&A conversational endpoint powered by CopilotAgent.
"""
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role
from app.domain.entities.user import UserRole
from ai.agents.copilot_agent import CopilotAgent
from ai.rag.retriever_factory import RetrieverFactory

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


class CopilotQueryRequest(BaseModel):
    query: str
    borrower_id: Optional[str] = None


@router.post("/query", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def query_copilot(
    req: CopilotQueryRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Conversational credit risk Q&A with Hybrid RAG using app-level Neo4j singleton."""
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    factory = RetrieverFactory(neo4j_client=neo4j_client)
    agent = CopilotAgent(retriever_factory=factory)
    result = await agent.run({
        "user_query": req.query,
        "borrower_id": req.borrower_id,
        "session": session,
    })
    return result
