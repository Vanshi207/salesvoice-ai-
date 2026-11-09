from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from salesvoice_common.security import InvalidToken, create_token, decode_token

from app.config import settings
from app.db import db
from app.models import User
from app.passwords import hash_password, verify_password
from app.schemas import LoginIn, RefreshIn, SignupIn, TokensOut, UserOut

router = APIRouter()


def issue_tokens(user: User) -> TokensOut:
    common = dict(user_id=user.id, role=user.role,
                  secret=settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return TokensOut(
        access_token=create_token(token_type="access",
                                  expires_in=timedelta(minutes=settings.access_token_minutes), **common),
        refresh_token=create_token(token_type="refresh",
                                   expires_in=timedelta(days=settings.refresh_token_days), **common),
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def signup(body: SignupIn, s: AsyncSession = Depends(db.session)):
    email = body.email.lower()

    existing = await s.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user_count = await s.scalar(select(func.count()).select_from(User))
    role = "admin" if user_count == 0 else "rep"

    user = User(email=email, name=body.name, password_hash=hash_password(body.password), role=role)
    s.add(user)
    await s.commit()
    return user


@router.post("/login", response_model=TokensOut)
async def login(body: LoginIn, s: AsyncSession = Depends(db.session)):
    user = await s.scalar(select(User).where(User.email == body.email.lower()))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return issue_tokens(user)


@router.post("/refresh", response_model=TokensOut)
async def refresh(body: RefreshIn, s: AsyncSession = Depends(db.session)):
    try:
        payload = decode_token(body.refresh_token, settings.jwt_secret,
                               settings.jwt_algorithm, expected_type="refresh")
    except InvalidToken:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    user = await s.get(User, payload.sub)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return issue_tokens(user)


@router.get("/me", response_model=UserOut)
async def me(x_user_id: str = Header(...), s: AsyncSession = Depends(db.session)):
    user = await s.get(User, x_user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user
