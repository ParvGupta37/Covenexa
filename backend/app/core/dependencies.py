"""
Dependency Injection providers for FastAPI endpoints.
Includes database session extraction and token security checks.
"""
from typing import AsyncGenerator, Callable, List

import structlog
from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.security import decode_token
from app.domain.entities.user import User, UserRole
from app.domain.value_objects.email import Email
from app.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from integrations.postgres.client import PostgresClient

logger = structlog.get_logger(__name__)

# Reusable HTTP Bearer token extractor
security_bearer = HTTPBearer()

# Singleton PostgresClient configuration
postgres_client = PostgresClient(
    database_url=settings.DATABASE_URL,
    pool_size=10,
    max_overflow=5,
)
postgres_client.initialize()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a database session from the connection pool."""
    async with postgres_client.session() as session:
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """
    Decodes the Bearer token, verifies its signature,
    and returns the User domain entity.
    """
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub", "")
        token_type: str = payload.get("type", "")
        
        if not user_id or token_type != "access":
            raise AuthenticationException("Invalid access token.")
            
    except JWTError as exc:
        logger.warning("token.decode.failed", error=str(exc))
        raise AuthenticationException("Could not validate credentials.")

    repo = UserRepositoryImpl(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise AuthenticationException("User account does not exist.")
    return user


def require_role(allowed_roles: List[UserRole]) -> Callable[[User], User]:
    """
    Role-Based Access Control (RBAC) dependency wrapper.
    Ensures the authenticated user possesses one of the allowed roles.
    """
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "rbac.authorization.failed",
                user_id=current_user.id,
                user_role=current_user.role.value,
                allowed=[r.value for r in allowed_roles],
            )
            raise ForbiddenException("Access denied. Insufficient permissions.")
        return current_user

    return dependency
