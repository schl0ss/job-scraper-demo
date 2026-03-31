from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, require_lead_ra
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserOut
from app.services.auth_service import authenticate_user, create_access_token, create_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token)


@router.post("/users", response_model=UserOut, status_code=201)
async def create_ra_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_lead_ra),
):
    """Lead RA only: create a new user account."""
    user = await create_user(db, body.email, body.password, body.role)
    return UserOut.model_validate(user)
