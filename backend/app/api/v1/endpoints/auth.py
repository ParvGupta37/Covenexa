"""
Authentication endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.auth.commands import LoginCommand, RegisterCommand
from app.application.auth.handlers import LoginHandler, RegisterHandler
from app.core.dependencies import get_db_session, get_current_user
from app.core.exceptions import AuthenticationException, EntityAlreadyExistsException
from app.core.schemas.auth import TokenResponseSchema, UserLoginSchema, UserRegisterSchema
from app.core.schemas.user import UserResponseSchema
from app.domain.entities.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
        # Password strength or validation error → 400 Bad Request
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except EntityAlreadyExistsException as exc:
        # Duplicate email → 409 Conflict
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
        return await handler.handle(command)
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
