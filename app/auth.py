"""Mounted pilot authentication and canonical Company onboarding."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.company import Company, User


SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logging.getLogger("passlib").setLevel(logging.ERROR)
auth_router = APIRouter()
security = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    company_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthenticatedUserResponse(BaseModel):
    """Safe profile returned to the browser; password material is excluded."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    company_id: UUID
    email: str
    full_name: str
    role: str
    language: str
    timezone: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _registration_error(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> HTTPException:
    return HTTPException(status_code=status_code, detail=detail)


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Atomically create the pilot's Company and its owner User."""
    email = request.email.strip().lower()
    company_name = request.company_name.strip()
    full_name = request.full_name.strip()
    if not email or "@" not in email:
        raise _registration_error("Geçerli bir e-posta adresi gerekli")
    if len(request.password) < 6:
        raise _registration_error("Şifre en az 6 karakter olmalı")
    if not company_name:
        raise _registration_error("Şirket adı gerekli")
    if db.query(User.id).filter(User.email == email).first() is not None:
        raise _registration_error("Bu e-posta adresi zaten kayıtlı")

    company = Company(name=company_name)
    owner = User(
        company=company,
        email=email,
        hashed_password=get_password_hash(request.password),
        full_name=full_name,
        role="owner",
    )
    try:
        db.add(owner)
        db.flush()
        db.commit()
        db.refresh(owner)
    except IntegrityError:
        db.rollback()
        # Covers concurrent duplicate-email registration without exposing SQL details.
        raise _registration_error("Bu e-posta adresi zaten kayıtlı")
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Kayıt tamamlanamadı. Lütfen tekrar deneyin.")

    return {
        "message": "Şirket ve sahip hesabı oluşturuldu",
        "user_id": str(owner.id),
        "company_id": str(owner.company_id),
        "email": owner.email,
        "role": owner.role,
    }


@auth_router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    email = request.email.strip().lower()
    user = db.query(User).filter(User.email == email, User.is_deleted.is_(False)).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz e-posta veya şifre")

    token = create_access_token({"user_id": str(user.id), "company_id": str(user.company_id)})
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user_id": str(user.id),
        "company_id": str(user.company_id),
    }


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kimlik doğrulama gerekli")
    try:
        user_id = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]).get("user_id")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz kimlik doğrulama bilgisi")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Geçersiz kimlik doğrulama bilgisi")
    user = db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kimlik doğrulama geçersiz")
    return user


def get_current_company_id(current_user: User = Depends(get_current_user)) -> UUID:
    """Canonical tenant authority. Never read a company ID from the client request."""
    return current_user.company_id


@auth_router.get("/me", response_model=AuthenticatedUserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if not credentials:
        return None
    try:
        user_id = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]).get("user_id")
    except JWTError:
        return None
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_deleted.is_(False)).first()
