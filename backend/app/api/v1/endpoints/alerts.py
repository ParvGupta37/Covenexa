"""
Alerts API Endpoints — Sprint 3.
Provides list, read-status update, and alert count APIs.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, require_role
from app.domain.entities.user import UserRole

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.get("/", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def list_alerts(
    unread_only: bool = False,
    borrower_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """Lists all severity-classified system alerts."""
    query = "SELECT * FROM alerts WHERE 1=1"
    params: Dict[str, Any] = {}
    if unread_only:
        query += " AND is_read = FALSE"
    if borrower_id:
        query += " AND borrower_id = :borrower_id"
        params["borrower_id"] = borrower_id

    query += " ORDER BY created_at DESC LIMIT 50"

    result = await session.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.post("/{alert_id}/read", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def mark_alert_read(
    alert_id: str,
    session: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Marks a specific alert as read."""
    await session.execute(
        text("UPDATE alerts SET is_read = TRUE WHERE id = :id"),
        {"id": alert_id}
    )
    await session.commit()
    return {"status": "success", "alert_id": alert_id}
