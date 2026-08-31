"""
Alerts API Endpoints — Sprint 3.
Provides list, read-status update, and alert count APIs.
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_current_user, require_role
from app.domain.entities.user import User, UserRole

router = APIRouter(prefix="/alerts", tags=["Alerts & Notifications"])
_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.get("/", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def list_alerts(
    unread_only: bool = False,
    borrower_id: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Lists all severity-classified system alerts for the user's organization."""
    user_org_id = current_user.organization_id if isinstance(current_user, User) else getattr(current_user, "organization_id", None)
    if user_org_id:
        query = """
            SELECT a.* FROM alerts a
            JOIN borrowers b ON a.borrower_id = b.id
            WHERE b.organization_id = :org_id AND b.is_archived = FALSE
        """
        params: Dict[str, Any] = {"org_id": user_org_id}
    else:
        query = """
            SELECT a.* FROM alerts a
            JOIN borrowers b ON a.borrower_id = b.id
            WHERE b.is_archived = FALSE
        """
        params = {}

    if unread_only:
        query += " AND a.is_read = FALSE"
    if borrower_id:
        query += " AND a.borrower_id = :borrower_id"
        params["borrower_id"] = borrower_id

    query += " ORDER BY a.created_at DESC LIMIT 50"

    result = await session.execute(text(query), params)
    rows = result.mappings().all()
    return [dict(r) for r in rows]


@router.post("/{alert_id}/read", dependencies=[Depends(require_role(_ALLOWED_ROLES))])
async def mark_alert_read(
    alert_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Marks a specific alert as read."""
    await session.execute(
        text("UPDATE alerts SET is_read = TRUE WHERE id = :id"),
        {"id": alert_id}
    )
    await session.commit()
    return {"status": "success", "alert_id": alert_id}
