"""Authentication routes and utilities.

Provides:
- /register    : create a new user (hashed password)
- /login       : username/password -> JWT access token
- /refresh     : refresh token (basic impl)
- Dependencies: get_current_user (from JWT)

Security:
- Uses passlib (bcrypt) for password hashing
- JWT tokens via PyJWT (use jose or other library in production)
- Access token lifetime controlled by settings

Note: This is a minimal but production-minded implementation. Replace
algorithms and key storage with secure KMS and rotate keys in production.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.user import UserCreate, UserRead, User
from app.models import db as models_db

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: Optional[datetime]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    q = select(models_db.User).where(models_db.User.username == username)
    res = await db.execute(q)
    return res.scalars().first()


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


async def get_current_user(db: AsyncSession = Depends(models_db.get_db), token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = await get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user


# Request/response schemas for register/login
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64)
    email: Optional[str]
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserRead)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(models_db.get_db)):
    """Create a new user with hashed password."""
    existing = await get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="username already registered")
    hashed = get_password_hash(payload.password)
    user = models_db.User(username=payload.username, email=payload.email or None, hashed_password=hashed)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserRead.from_orm(user)


@router.post("/login", response_model=LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(models_db.get_db)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return LoginResponse(access_token=access_token)


@router.get("/me", response_model=UserRead)
async def me(current_user: User = Depends(get_current_user)):
    return UserRead.from_orm(current_user)
