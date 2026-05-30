"""WorkFlow — Auth Service."""
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile

logger = structlog.get_logger()


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = UserRepository(session)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        if await self.repo.email_exists(data.email):
            raise ConflictException(f"Email '{data.email}' is already registered")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            department=data.department,
        )
        user = await self.repo.create(user)
        logger.info("auth.register", user_id=str(user.id), role=user.role)
        return self._build_token_response(user)

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedException("Account is deactivated")

        logger.info("auth.login", user_id=str(user.id), role=user.role)
        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        token = create_access_token(
            user_id=user.id, role=user.role, email=user.email
        )
        return TokenResponse(
            access_token=token,
            expires_in=settings.jwt_access_token_expire_minutes * 60,
            user=UserProfile.model_validate(user),
        )
