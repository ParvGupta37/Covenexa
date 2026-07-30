"""
Authentication application command handlers.
"""
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.commands import LoginCommand, RegisterCommand
from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException
from app.core.security import create_access_token, create_refresh_token, hash_password, verify_password
from app.domain.entities.user import User, UserRole
from app.domain.services.auth_domain_service import AuthDomainService
from app.domain.value_objects.email import Email
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl

logger = structlog.get_logger(__name__)


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
        
        logger.info("auth.login.success", user_id=user.id)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
