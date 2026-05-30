"""WorkFlow — Auth Router."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import CurrentUser, get_current_user
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserProfile
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Register a new user (manager or employee). Returns JWT."""
    return await AuthService(session).register(data)


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Login with email + password. Returns JWT."""
    return await AuthService(session).login(data)


@router.get("/me", response_model=UserProfile)
async def me(current: CurrentUser = Depends(get_current_user)) -> UserProfile:
    """Return the currently authenticated user's profile."""
    return UserProfile.model_validate(current.user)
