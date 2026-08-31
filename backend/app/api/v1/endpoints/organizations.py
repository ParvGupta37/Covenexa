"""
Organization endpoints.
"""
from datetime import datetime, timezone
import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db_session, get_current_user, require_role
from app.core.exceptions import EntityAlreadyExistsException, EntityNotFoundException, ForbiddenException
from app.core.schemas.auth import (
    InvitationResponseSchema,
    MemberInviteSchema,
    MemberRoleUpdateSchema,
)
from app.core.schemas.organization import (
    OrganizationCreateSchema,
    OrganizationDetailSchema,
    OrganizationResponseSchema,
    OrganizationStatsSchema,
)
from app.core.schemas.user import UserResponseSchema
from app.domain.entities.invitation import Invitation
from app.domain.entities.organization import Organization
from app.domain.entities.user import User, UserRole
from app.infrastructure.orm.borrower_orm import BorrowerORM
from app.infrastructure.orm.loan_orm import LoanORM
from app.infrastructure.orm.agreement_orm import AgreementORM
from app.infrastructure.repositories.invitation_repository_impl import InvitationRepositoryImpl
from app.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

router = APIRouter(prefix="/organizations", tags=["Organizations"])


_ALLOWED_ROLES = [UserRole.ADMIN, UserRole.MANAGER, UserRole.ANALYST]


@router.post(
    "/",
    response_model=OrganizationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def create_organization(
    payload: OrganizationCreateSchema,
    session: AsyncSession = Depends(get_db_session),
) -> Organization:
    """Create a new Organization. Restricted to ADMIN role."""
    repo = OrganizationRepositoryImpl(session)

    existing = await repo.get_by_name(payload.name)
    if existing:
        raise EntityAlreadyExistsException("Organization", payload.name)

    org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name,
        industry=payload.industry,
    )
    return await repo.add(org)


@router.get(
    "/",
    response_model=list[OrganizationResponseSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_organizations(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Organization]:
    """
    List organizations.
    If current_user has an organization_id, returns ONLY their organization.
    Super-admins without org filter can see all.
    """
    repo = OrganizationRepositoryImpl(session)
    if current_user.organization_id:
        org = await repo.get_by_id(current_user.organization_id)
        return [org] if org else []
    return await repo.get_all()


@router.get(
    "/{org_id}",
    response_model=OrganizationDetailSchema,
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def get_organization(
    org_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get a single organization with statistics about its associated data."""
    # Tenant check: user must belong to this organization unless they are global admin without org
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You do not have access to this organization.")

    repo = OrganizationRepositoryImpl(session)
    org = await repo.get_by_id(org_id)
    if not org:
        raise EntityNotFoundException("Organization", org_id)

    # Count active borrowers
    borrower_count_result = await session.execute(
        select(func.count()).where(
            BorrowerORM.organization_id == org_id,
            BorrowerORM.is_archived == False,
        )
    )
    borrower_count = borrower_count_result.scalar() or 0

    # Count active loans via active borrowers
    loan_count_result = await session.execute(
        select(func.count(LoanORM.id)).join(
            BorrowerORM, LoanORM.borrower_id == BorrowerORM.id
        ).where(
            BorrowerORM.organization_id == org_id,
            BorrowerORM.is_archived == False,
            LoanORM.is_archived == False,
        )
    )
    loan_count = loan_count_result.scalar() or 0

    # Count agreements via loans via borrowers
    agreement_count_result = await session.execute(
        text("""
            SELECT COUNT(a.id)
            FROM agreements a
            JOIN loans l ON a.loan_id = l.id
            JOIN borrowers b ON l.borrower_id = b.id
            WHERE b.organization_id = :org_id
        """),
        {"org_id": org_id},
    )
    agreement_count = agreement_count_result.scalar() or 0

    return {
        "id": org.id,
        "name": org.name,
        "industry": org.industry,
        "created_at": org.created_at,
        "stats": {
            "borrower_count": borrower_count,
            "loan_count": loan_count,
            "agreement_count": agreement_count,
        },
    }


# ── MEMBER MANAGEMENT ─────────────────────────────────────────────

@router.get(
    "/{org_id}/members",
    response_model=list[UserResponseSchema],
    dependencies=[Depends(require_role(_ALLOWED_ROLES))],
)
async def list_organization_members(
    org_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[User]:
    """List all team members of an organization."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You do not have access to view members of this organization.")

    user_repo = UserRepositoryImpl(session)
    return await user_repo.get_by_organization_id(org_id)


@router.post(
    "/{org_id}/invitations",
    response_model=InvitationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def invite_member(
    org_id: str,
    payload: MemberInviteSchema,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Invite a new member to the organization (Admin only)."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot invite members to an organization other than your own.")

    user_repo = UserRepositoryImpl(session)
    invite_repo = InvitationRepositoryImpl(session)

    # Check if user already exists
    from app.domain.value_objects.email import Email
    existing_user = await user_repo.get_by_email(Email(payload.email.lower()))
    if existing_user:
        raise EntityAlreadyExistsException("User with this email already exists in the system.", payload.email)

    # Parse requested role
    try:
        role_enum = UserRole(payload.role.upper())
    except ValueError:
        role_enum = UserRole.ANALYST

    # Generate token and invitation
    token = secrets.token_urlsafe(32)
    invitation = Invitation(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        email=payload.email.lower(),
        name=payload.name,
        role=role_enum,
        token=token,
        status="PENDING",
    )
    created_invite = await invite_repo.add(invitation)

    base_url = str(request.base_url).rstrip("/")
    invite_url = f"/register?invite={token}"

    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="member.invited",
        resource_type="organization",
        resource_id=org_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={"invited_email": payload.email, "role": role_enum.value},
    )

    return {
        "id": created_invite.id,
        "organization_id": created_invite.organization_id,
        "email": created_invite.email,
        "name": created_invite.name,
        "role": created_invite.role.value if hasattr(created_invite.role, "value") else str(created_invite.role),
        "token": created_invite.token,
        "status": created_invite.status,
        "created_at": created_invite.created_at,
        "expires_at": created_invite.expires_at,
        "invite_url": invite_url,
    }


@router.get(
    "/{org_id}/invitations",
    response_model=list[InvitationResponseSchema],
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def list_organization_invitations(
    org_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> list[Invitation]:
    """List pending invitations for an organization (Admin only)."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot view invitations for another organization.")

    invite_repo = InvitationRepositoryImpl(session)
    return await invite_repo.get_by_organization_id(org_id)


@router.delete(
    "/{org_id}/invitations/{invite_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def revoke_invitation(
    org_id: str,
    invite_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Cancel / Revoke a pending invitation (Admin only)."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot manage invitations for another organization.")

    invite_repo = InvitationRepositoryImpl(session)
    invitation = await invite_repo.get_by_id(invite_id)
    if not invitation or invitation.organization_id != org_id:
        raise EntityNotFoundException("Invitation", invite_id)

    await invite_repo.delete(invite_id)


@router.patch(
    "/{org_id}/members/{user_id}/role",
    response_model=UserResponseSchema,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def update_member_role(
    org_id: str,
    user_id: str,
    payload: MemberRoleUpdateSchema,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> User:
    """Change a member's role (Admin only)."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot modify members in another organization.")

    user_repo = UserRepositoryImpl(session)
    member = await user_repo.get_by_id(user_id)
    if not member or member.organization_id != org_id:
        raise EntityNotFoundException("Member", user_id)

    # Validate target role
    try:
        new_role = UserRole(payload.role.upper())
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid role '{payload.role}'. Must be ADMIN, MANAGER, or ANALYST.")

    # Last-Admin protection: Prevent demoting the only admin
    if member.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        all_members = await user_repo.get_by_organization_id(org_id)
        admin_count = sum(1 for m in all_members if m.role == UserRole.ADMIN)
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot demote the last Administrator of the organization."
            )

    member.update_role(new_role)
    updated = await user_repo.update(member)

    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="member.role_updated",
        resource_type="organization",
        resource_id=org_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={"target_user_id": user_id, "new_role": new_role.value},
    )

    return updated


@router.delete(
    "/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_role([UserRole.ADMIN]))],
)
async def remove_member(
    org_id: str,
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a member from the organization (Admin only)."""
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot remove members from another organization.")

    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the organization. Transfer ownership or delete the organization instead."
        )

    user_repo = UserRepositoryImpl(session)
    member = await user_repo.get_by_id(user_id)
    if not member or member.organization_id != org_id:
        raise EntityNotFoundException("Member", user_id)

    # Last-Admin protection: Prevent removing the last admin
    if member.role == UserRole.ADMIN:
        all_members = await user_repo.get_by_organization_id(org_id)
        admin_count = sum(1 for m in all_members if m.role == UserRole.ADMIN)
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last Administrator of the organization."
            )

    # Unlink member from organization (or delete user account)
    member.organization_id = None
    await user_repo.update(member)

    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="member.removed",
        resource_type="organization",
        resource_id=org_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={"removed_user_id": user_id, "removed_email": str(member.email)},
    )


# ── DELETE ORGANIZATION ──────────────────────────────────────────

@router.delete(
    "/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_organization(
    org_id: str,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_role([UserRole.ADMIN])),
) -> None:
    """
    Permanently delete an organization and all its cascading data.
    Restricted to ADMIN role only.
    """
    if current_user.organization_id and current_user.organization_id != org_id:
        raise ForbiddenException("You cannot delete another organization.")

    repo = OrganizationRepositoryImpl(session)
    org = await repo.get_by_id(org_id)
    if not org:
        raise EntityNotFoundException("Organization", org_id)

    org_name = org.name

    # Log the deletion audit event BEFORE destroying data
    from app.api.v1.endpoints.audit import log_audit_event
    await log_audit_event(
        action="organization.deleted",
        resource_type="organization",
        resource_id=org_id,
        user_id=current_user.id,
        user_email=str(current_user.email),
        details={
            "org_name": org_name,
            "deleted_by": current_user.name,
            "ip": request.client.host if request.client else None,
        },
    )

    # Delete — PostgreSQL CASCADE handles all child data
    await repo.delete(org_id)
