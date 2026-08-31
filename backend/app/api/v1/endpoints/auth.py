"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.commands import LoginCommand, RegisterCommand
from app.application.auth.handlers import (
    InviteAcceptHandler,
    LoginHandler,
    OrgSignupHandler,
    RegisterHandler,
)
from app.core.dependencies import get_db_session, get_current_user
from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException, EntityNotFoundException
from app.core.schemas.auth import (
    InviteAcceptSchema,
    OrgSignupSchema,
    TokenResponseSchema,
    UserLoginSchema,
    UserRegisterSchema,
)
from app.core.schemas.user import UserResponseSchema
from app.domain.entities.user import User
from app.infrastructure.repositories.invitation_repository_impl import InvitationRepositoryImpl
from app.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup-org", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
async def signup_organization(
    payload: OrgSignupSchema,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Register a new Lender Organization and create its Owner / Admin account.
    Returns access & refresh tokens to log the new user straight in.
    """
    handler = OrgSignupHandler(session)
    try:
        res = await handler.handle(
            name=payload.name,
            email=payload.email.lower(),
            password=payload.password,
            org_name=payload.organization_name,
            org_industry=payload.organization_industry,
        )
        return res
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EntityAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get("/verify-invite/{token}")
async def verify_invite_token(
    token: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Validate an invitation token and return organization metadata.
    """
    invite_repo = InvitationRepositoryImpl(session)
    org_repo = OrganizationRepositoryImpl(session)

    invitation = await invite_repo.get_by_token(token)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid or non-existent invitation token.")

    if invitation.status != "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This invitation has already been {invitation.status.lower()}."
        )

    org = await org_repo.get_by_id(invitation.organization_id)
    return {
        "email": invitation.email,
        "name": invitation.name,
        "role": invitation.role.value if hasattr(invitation.role, "value") else str(invitation.role),
        "organization_id": invitation.organization_id,
        "organization_name": org.name if org else "Unknown Organization",
        "status": invitation.status,
    }


@router.post("/accept-invite", response_model=TokenResponseSchema, status_code=status.HTTP_201_CREATED)
async def accept_invitation(
    payload: InviteAcceptSchema,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Accept an invitation token, creating the user under that organization and returning JWT tokens.
    """
    handler = InviteAcceptHandler(session)
    try:
        return await handler.handle(
            token=payload.token,
            name=payload.name,
            password=payload.password,
        )
    except EntityNotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EntityAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterSchema,
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Register a new user profile on the platform."""
    command = RegisterCommand(
        name=payload.name,
        email=payload.email.lower(),
        password=payload.password,
        role=payload.role,
    )
    handler = RegisterHandler(session)
    try:
        return await handler.handle(command)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EntityAlreadyExistsException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.post("/login", response_model=TokenResponseSchema)
async def login(
    payload: UserLoginSchema,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Authenticate email and password, returning JWT access & refresh tokens."""
    command = LoginCommand(email=payload.email.lower(), password=payload.password)
    handler = LoginHandler(session)
    try:
        res = await handler.handle(command)
        user_info = res.get("user", {})
        from app.api.v1.endpoints.audit import log_audit_event
        await log_audit_event(
            action="user_login",
            resource_type="auth",
            user_id=user_info.get("id"),
            user_email=payload.email,
            details={"email": payload.email},
        )
        return res
    except AuthenticationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponseSchema)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """Return the authenticated user profile."""
    return current_user
