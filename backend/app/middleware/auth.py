"""WorkFlow — Auth Middleware (FastAPI dependencies)."""
import uuid

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import Role, User
from app.repositories.user_repository import UserRepository

logger = structlog.get_logger()
security = HTTPBearer()


class CurrentUser:
    """Dependency-injected current user with role helpers."""

    def __init__(self, user: User) -> None:
        self.user = user

    @property
    def id(self) -> uuid.UUID:
        return self.user.id

    @property
    def role(self) -> Role:
        return self.user.role

    @property
    def is_manager(self) -> bool:
        return self.user.role == Role.MANAGER

    @property
    def is_employee(self) -> bool:
        return self.user.role == Role.EMPLOYEE


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Verify JWT and return the active user. Raises 401 on failure."""
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise UnauthorizedException("Invalid or expired token")

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise UnauthorizedException("User not found or inactive")

    return CurrentUser(user)


async def require_manager(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Raises 403 if the current user is not a manager."""
    if not current.is_manager:
        raise ForbiddenException("Manager access required")
    return current


async def require_employee(
    current: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """Raises 403 if the current user is not an employee."""
    if not current.is_employee:
        raise ForbiddenException("Employee access required")
    return current
