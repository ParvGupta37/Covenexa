"""
Domain-specific application exceptions mapping clean HTTP status codes.
"""
from fastapi import HTTPException, status


class DomainException(HTTPException):
    """Base domain exception class."""
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(status_code=status_code, detail=detail)


class AuthenticationException(DomainException):
    """Raised on authentication failures."""
    def __init__(self, detail: str = "Invalid credentials.") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(DomainException):
    """Raised when access permissions are insufficient."""
    def __init__(self, detail: str = "Access denied.") -> None:
        super().__init__(detail=detail, status_code=status.HTTP_403_FORBIDDEN)


class EntityNotFoundException(DomainException):
    """Raised when request target entity does not exist in store."""
    def __init__(self, entity_name: str, entity_id: str) -> None:
        super().__init__(
            detail=f"{entity_name} with key {entity_id} was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class EntityAlreadyExistsException(DomainException):
    """Raised when attempting to insert duplicate key values."""
    def __init__(self, entity_name: str, duplicate_value: str) -> None:
        super().__init__(
            detail=f"{entity_name} with identifier '{duplicate_value}' already exists.",
            status_code=status.HTTP_409_CONFLICT,
        )
