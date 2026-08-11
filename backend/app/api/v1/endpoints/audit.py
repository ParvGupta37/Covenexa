"""
Audit Logs API Endpoints & Helper — Sprint 4.
Provides APIs to list activity logs and helper functions to record audit events across system operations.
"""
from typing import Any, List, Optional
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role, get_current_user
from app.domain.entities.user import User, UserRole

router = APIRouter(prefix="/audit", tags=["Audit Logs"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


class AuditLogSchema(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime


async def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    session: Optional[Any] = None,  # kept for backwards-compat but ignored
) -> None:
    """Persist audit log events via an independent DB session."""
    from app.core.dependencies import postgres_client
    try:
        log_id = str(uuid.uuid4())
        dt_str = json.dumps(details) if details else None
        now = datetime.now(timezone.utc)

        async with postgres_client.session() as s:
            await s.execute(
                text("""
                    INSERT INTO audit_logs 
                    (id, user_id, user_email, action, resource_type, resource_id, details, ip_address, created_at)
                    VALUES (:id, :uid, :uemail, :action, :rtype, :rid, :details, :ip, :now)
                """),
                {
                    "id": log_id,
                    "uid": user_id,
                    "uemail": user_email,
                    "action": action,
                    "rtype": resource_type,
                    "rid": resource_id,
                    "details": dt_str,
                    "ip": ip_address,
                    "now": now,
                }
            )
    except Exception as e:
        print(f"[AuditLog Error] Failed to record audit log: {e}")


@router.get(
    "/",
    response_model=List[AuditLogSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
) -> List[dict]:
    """Retrieve audit activity history with filtering and pagination."""
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = {"limit": limit}

    if action:
        query += " AND action = :action"
        params["action"] = action
    if resource_type:
        query += " AND resource_type = :resource_type"
        params["resource_type"] = resource_type

    query += " ORDER BY created_at DESC LIMIT :limit"

    result = await session.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(r) for r in rows]
