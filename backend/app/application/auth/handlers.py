"""
Authentication application command handlers.
"""
from datetime import datetime, timezone
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.commands import LoginCommand, RegisterCommand
from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException, EntityNotFoundException
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.domain.entities.organization import Organization
from app.domain.entities.user import User, UserRole
from app.domain.services.auth_domain_service import AuthDomainService
from app.domain.value_objects.email import Email
from app.infrastructure.repositories.invitation_repository_impl import InvitationRepositoryImpl
from app.infrastructure.repositories.organization_repository_impl import OrganizationRepositoryImpl
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

logger = structlog.get_logger(__name__)


class OrgSignupHandler:
    """
    Handles first-time registration of a new Lender Organization + its Admin Owner.
    """
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepositoryImpl(session)
        self._org_repo = OrganizationRepositoryImpl(session)

    async def handle(
        self,
        name: str,
        email: str,
        password: str,
        org_name: str,
        org_industry: str = "Private Credit"
    ) -> dict:
        email_vo = Email(email)

        # Validate password strength
        if not AuthDomainService.is_strong_password(password):
            raise ValueError(
                "Password must be at least 8 characters long, contain uppercase, "
                "lowercase, digit, and special character."
            )

        # Check existing user
        existing_user = await self._user_repo.get_by_email(email_vo)
        if existing_user:
            raise EntityAlreadyExistsException("User", email)

        # Check or create organization
        existing_org = await self._org_repo.get_by_name(org_name)
        if existing_org:
            raise EntityAlreadyExistsException("Organization", org_name)

        org_id = str(uuid.uuid4())
        org = Organization(
            id=org_id,
            name=org_name,
            industry=org_industry,
        )
        created_org = await self._org_repo.add(org)

        # Create First User as ADMIN & Owner of this organization
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=name,
            email=email_vo,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            organization_id=created_org.id,
        )
        created_user = await self._user_repo.add(user)

        # Issue tokens
        access_token = create_access_token(subject=created_user.id, role=created_user.role.value)
        refresh_token = create_refresh_token(subject=created_user.id)

        logger.info(
            "auth.org_signup.success",
            user_id=created_user.id,
            org_id=created_org.id,
            org_name=created_org.name,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": created_user.id,
                "name": created_user.name,
                "email": str(created_user.email),
                "role": created_user.role.value,
                "organization_id": created_org.id,
                "created_at": created_user.created_at,
            },
            "organization": {
                "id": created_org.id,
                "name": created_org.name,
                "industry": created_org.industry,
            }
        }


class InviteAcceptHandler:
    """
    Handles user onboarding when accepting an invitation from an existing organization.
    """
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepositoryImpl(session)
        self._invite_repo = InvitationRepositoryImpl(session)
        self._org_repo = OrganizationRepositoryImpl(session)

    async def handle(self, token: str, name: str, password: str) -> dict:
        invitation = await self._invite_repo.get_by_token(token)
        if not invitation:
            raise EntityNotFoundException("Invitation", token)

        if invitation.status != "PENDING":
            raise ValueError(f"Invitation has already been {invitation.status.lower()}.")

        if invitation.expires_at and invitation.expires_at < datetime.now(timezone.utc):
            raise ValueError("Invitation link has expired.")

        email_vo = Email(invitation.email)

        # Validate password
        if not AuthDomainService.is_strong_password(password):
            raise ValueError(
                "Password must be at least 8 characters long, contain uppercase, "
                "lowercase, digit, and special character."
            )

        existing_user = await self._user_repo.get_by_email(email_vo)
        if existing_user:
            raise EntityAlreadyExistsException("User", invitation.email)

        # Create member user with the organization_id and assigned role
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=name,
            email=email_vo,
            password_hash=hash_password(password),
            role=invitation.role,
            organization_id=invitation.organization_id,
        )
        created_user = await self._user_repo.add(user)

        # Mark invitation as ACCEPTED
        invitation.status = "ACCEPTED"
        await self._invite_repo.update(invitation)

        # Tokens
        access_token = create_access_token(subject=created_user.id, role=created_user.role.value)
        refresh_token = create_refresh_token(subject=created_user.id)

        logger.info(
            "auth.invite_accepted",
            user_id=created_user.id,
            org_id=invitation.organization_id,
            role=invitation.role.value,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": created_user.id,
                "name": created_user.name,
                "email": str(created_user.email),
                "role": created_user.role.value,
                "organization_id": invitation.organization_id,
                "created_at": created_user.created_at,
            }
        }


class RegisterHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepositoryImpl(session)

    async def handle(self, command: RegisterCommand) -> User:
        # Validate email syntax at Domain VO boundary
        email_vo = Email(command.email)
        
        # Check password strength at domain service boundary
        if not AuthDomainService.is_strong_password(command.password):
            raise ValueError(
                "Password must be at least 8 characters long, contain uppercase, "
                "lowercase, digit, and special character."
            )

        existing = await self._repo.get_by_email(email_vo)
        if existing:
            raise EntityAlreadyExistsException("User", command.email)

        # Parse role
        try:
            role_enum = UserRole(command.role.upper())
        except ValueError:
            role_enum = UserRole.ANALYST

        # Create user
        user = User(
            id=str(uuid.uuid4()),
            name=command.name,
            email=email_vo,
            password_hash=hash_password(command.password),
            role=role_enum,
        )
        return await self._repo.add(user)


class LoginHandler:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = UserRepositoryImpl(session)

    async def handle(self, command: LoginCommand) -> dict:
        email_vo = Email(command.email)
        user = await self._repo.get_by_email(email_vo)
        
        if not user or not verify_password(command.password, user.password_hash):
            logger.warning("auth.login.failed", email=command.email)
            raise AuthenticationException()

        # Create credentials tokens
        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token = create_refresh_token(subject=user.id)
        
        logger.info("auth.login.success", user_id=user.id, org_id=user.organization_id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "name": user.name,
                "email": str(user.email),
                "role": user.role.value,
                "organization_id": user.organization_id,
                "created_at": user.created_at,
            }
        }
