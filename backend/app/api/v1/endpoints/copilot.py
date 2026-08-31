"""
AI Copilot Endpoints — Sprint 4 (Persistent Conversations & Multi-Tenant History).
Provides:
- Conversational credit risk Q&A with Hybrid RAG and full message persistence
- List, create, retrieve, and delete Copilot conversations
- Full evidence/citation persistence and strict tenant isolation
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, get_db_session, require_role
from app.core.exceptions import EntityNotFoundException, ForbiddenException
from app.domain.entities.user import User, UserRole
from app.infrastructure.orm.borrower_orm import BorrowerORM
from app.infrastructure.orm.copilot_orm import CopilotConversationORM, CopilotMessageORM
from ai.agents.copilot_agent import CopilotAgent
from ai.rag.retriever_factory import RetrieverFactory

router = APIRouter(prefix="/copilot", tags=["AI Copilot"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


# ── SCHEMAS ─────────────────────────────────────────────────────────

class CopilotQueryRequest(BaseModel):
    query: str
    borrower_id: Optional[str] = None
    conversation_id: Optional[str] = None


class CopilotCreateConversationRequest(BaseModel):
    borrower_id: Optional[str] = None
    title: Optional[str] = "New Conversation"


class CopilotMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    citations: Optional[List[str]] = None
    hybrid_retrieval_status: Optional[Dict[str, bool]] = None
    evidence_sources: Optional[Dict[str, int]] = None
    message_index: int
    created_at: datetime


class CopilotConversationSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: Optional[str] = None
    borrower_id: Optional[str] = None
    title: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime


class CopilotConversationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: Optional[str] = None
    borrower_id: Optional[str] = None
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[CopilotMessageResponse] = []


# ── ENDPOINTS ───────────────────────────────────────────────────────

@router.get(
    "/conversations",
    response_model=List[CopilotConversationSummaryResponse],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_conversations(
    borrower_id: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> List[CopilotConversationSummaryResponse]:
    """
    List Copilot conversations for the authenticated user only.
    Optionally filters by borrower context.
    """
    if not current_user.organization_id:
        return []

    stmt = (
        select(
            CopilotConversationORM,
            func.count(CopilotMessageORM.id).label("message_count"),
        )
        .outerjoin(CopilotMessageORM, CopilotMessageORM.conversation_id == CopilotConversationORM.id)
        .where(
            CopilotConversationORM.organization_id == current_user.organization_id,
            CopilotConversationORM.user_id == current_user.id,
        )
    )

    if borrower_id:
        stmt = stmt.where(CopilotConversationORM.borrower_id == borrower_id)

    stmt = (
        stmt.group_by(CopilotConversationORM.id)
        .order_by(CopilotConversationORM.updated_at.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    summaries = []
    for conv, count in rows:
        summaries.append(
            CopilotConversationSummaryResponse(
                id=conv.id,
                organization_id=conv.organization_id,
                user_id=conv.user_id,
                borrower_id=conv.borrower_id,
                title=conv.title,
                message_count=count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )
    return summaries


@router.post(
    "/conversations",
    response_model=CopilotConversationDetailResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def create_conversation(
    req: CopilotCreateConversationRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CopilotConversationDetailResponse:
    """
    Create a new empty Copilot conversation scoped to the tenant and user.
    """
    if not current_user.organization_id:
        raise ForbiddenException("User must belong to an organization to create conversations.")

    # Validate borrower if provided
    if req.borrower_id:
        borrower_stmt = select(BorrowerORM).where(
            BorrowerORM.id == req.borrower_id,
            BorrowerORM.organization_id == current_user.organization_id,
        )
        b_res = await session.execute(borrower_stmt)
        if not b_res.scalar_one_or_none():
            raise EntityNotFoundException("Borrower", req.borrower_id)

    new_conv = CopilotConversationORM(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        borrower_id=req.borrower_id,
        title=req.title or "New Conversation",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(new_conv)
    await session.commit()
    await session.refresh(new_conv)

    return CopilotConversationDetailResponse(
        id=new_conv.id,
        organization_id=new_conv.organization_id,
        user_id=new_conv.user_id,
        borrower_id=new_conv.borrower_id,
        title=new_conv.title,
        created_at=new_conv.created_at,
        updated_at=new_conv.updated_at,
        messages=[],
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=CopilotConversationDetailResponse,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> CopilotConversationDetailResponse:
    """
    Retrieve full conversation history and structured citations with user and tenant verification.
    """
    stmt = (
        select(CopilotConversationORM)
        .options(selectinload(CopilotConversationORM.messages))
        .where(
            CopilotConversationORM.id == conversation_id,
            CopilotConversationORM.organization_id == current_user.organization_id,
            CopilotConversationORM.user_id == current_user.id,
        )
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise EntityNotFoundException("CopilotConversation", conversation_id)

    # Sort messages deterministically
    sorted_messages = sorted(conv.messages, key=lambda m: (m.message_index, m.created_at))

    return CopilotConversationDetailResponse(
        id=conv.id,
        organization_id=conv.organization_id,
        user_id=conv.user_id,
        borrower_id=conv.borrower_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[
            CopilotMessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                citations=m.citations,
                hybrid_retrieval_status=m.hybrid_retrieval_status,
                evidence_sources=m.evidence_sources,
                message_index=m.message_index,
                created_at=m.created_at,
            )
            for m in sorted_messages
        ],
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def delete_conversation(
    conversation_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Delete a conversation and its messages scoped to the user.
    """
    stmt = select(CopilotConversationORM).where(
        CopilotConversationORM.id == conversation_id,
        CopilotConversationORM.organization_id == current_user.organization_id,
        CopilotConversationORM.user_id == current_user.id,
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()
    if not conv:
        raise EntityNotFoundException("CopilotConversation", conversation_id)

    await session.delete(conv)
    await session.commit()
    return {"status": "deleted", "id": conversation_id}


@router.post("/query", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def query_copilot(
    req: CopilotQueryRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Conversational credit risk Q&A with Hybrid RAG.
    Persists user query, synthesized response, and citations to database.
    """
    if not current_user.organization_id:
        raise ForbiddenException("User must belong to an organization to query Copilot.")

    # 1. Resolve or create target conversation
    conv: Optional[CopilotConversationORM] = None

    if req.conversation_id:
        conv_stmt = (
            select(CopilotConversationORM)
            .options(selectinload(CopilotConversationORM.messages))
            .where(
                CopilotConversationORM.id == req.conversation_id,
                CopilotConversationORM.organization_id == current_user.organization_id,
                CopilotConversationORM.user_id == current_user.id,
            )
        )
        c_res = await session.execute(conv_stmt)
        conv = c_res.scalar_one_or_none()
        if not conv:
            raise EntityNotFoundException("CopilotConversation", req.conversation_id)
    else:
        # Create a new conversation for this new chat session
        title_snippet = req.query.strip().replace("\n", " ")
        clean_title = (title_snippet[:45] + "…") if len(title_snippet) > 45 else title_snippet
        conv = CopilotConversationORM(
            id=str(uuid.uuid4()),
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            borrower_id=req.borrower_id,
            title=clean_title or "Credit Risk Inquiry",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(conv)
        await session.flush()
        await session.refresh(conv, attribute_names=["messages"])

    # Compute next message indices
    current_count = len(conv.messages) if conv.messages else 0
    user_idx = current_count + 1
    assistant_idx = current_count + 2

    # 2. Persist user message
    user_msg = CopilotMessageORM(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="user",
        content=req.query,
        message_index=user_idx,
        created_at=datetime.now(timezone.utc),
    )
    session.add(user_msg)

    # 3. Execute Copilot agent pipeline
    neo4j_client = getattr(request.app.state, "neo4j_client", None)
    factory = RetrieverFactory(neo4j_client=neo4j_client)
    agent = CopilotAgent(retriever_factory=factory)
    result = await agent.run({
        "user_query": req.query,
        "borrower_id": req.borrower_id or conv.borrower_id,
        "session": session,
    })

    assistant_content = result.get("response", "")
    citations_data = result.get("citations", [])
    hybrid_status_data = result.get("hybrid_retrieval_status", {})
    evidence_sources_data = result.get("evidence_sources", {})

    # 4. Persist assistant response with citations
    assistant_msg = CopilotMessageORM(
        id=str(uuid.uuid4()),
        conversation_id=conv.id,
        role="assistant",
        content=assistant_content,
        citations=citations_data,
        hybrid_retrieval_status=hybrid_status_data,
        evidence_sources=evidence_sources_data,
        message_index=assistant_idx,
        created_at=datetime.now(timezone.utc),
    )
    session.add(assistant_msg)

    # 5. Update conversation title if default and update timestamp
    if conv.title in ("New Conversation", "Credit Risk Inquiry"):
        title_snippet = req.query.strip().replace("\n", " ")
        conv.title = (title_snippet[:45] + "…") if len(title_snippet) > 45 else title_snippet
    conv.updated_at = datetime.now(timezone.utc)

    await session.commit()

    return {
        "conversation_id": conv.id,
        "message_id": assistant_msg.id,
        "query": req.query,
        "response": assistant_content,
        "citations": citations_data,
        "hybrid_retrieval_status": hybrid_status_data,
        "evidence_sources": evidence_sources_data,
    }
