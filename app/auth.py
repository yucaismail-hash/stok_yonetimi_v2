from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.database import get_db
from app.models import *
import os
import logging
logging.getLogger("passlib").setLevel(logging.ERROR)

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

auth_router = APIRouter()
security = HTTPBearer(auto_error=False)


# ✅ BU FONKSİYONLAR TANIMLI OLMALI
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""
    company_name: str = ""
    sector_id: Optional[int] = None
    # 🆕 Fatura bilgileri
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    billing_country: Optional[str] = "TR"
    billing_postal_code: Optional[str] = None
    tax_id: Optional[str] = None
    tax_office: Optional[str] = None
    identity_number: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@auth_router.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı")
    
    sector_id = request.sector_id if request.sector_id else 32
    
    new_user = User(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        full_name=request.full_name,
        company_name=request.company_name,
        sector_id=sector_id,
        token_balance=100,
        # 🆕 Fatura bilgileri
        billing_address=request.billing_address,
        billing_city=request.billing_city,
        billing_state=request.billing_state,
        billing_country=request.billing_country or "TR",
        billing_postal_code=request.billing_postal_code,
        tax_id=request.tax_id,
        tax_office=request.tax_office,
        identity_number=request.identity_number,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {
        "msg": "Kullanıcı oluşturuldu",
        "user_id": new_user.id,
        "token_balance": new_user.token_balance,
        "full_name": new_user.full_name,
        "company_name": new_user.company_name,
        "sector_id": new_user.sector_id
    }


@auth_router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Geçersiz email veya şifre")
    
    token = create_access_token({"sub": user.email, "user_id": user.id})
    
    sector_name = None
    if user.sector_id:
        sector = db.query(Sector).filter(Sector.id == user.sector_id).first()
        sector_name = sector.name if sector else None
    
    return {
        "access_token": token,
        "token_type": "Bearer",
        "user_id": user.id,
        "token_balance": user.token_balance,
        "full_name": user.full_name or "",
        "company_name": user.company_name or "",
        "sector_id": user.sector_id,
        "sector_name": sector_name
    }


@auth_router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: Session = Depends(get_db)
):

    
    if not credentials:
        raise HTTPException(status_code=401, detail="Token gerekli")
    
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Geçersiz token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    
    return user


# ✅ get_current_user_optional - DÜZELTİLMİŞ
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Token varsa kullanıcıyı döndür, yoksa None döndür.
    Upload gibi opsiyonel token gerektiren endpoint'ler için.
    """
    if not credentials:
        print("⚠️ Token yok, anonim kullanıcı olarak devam")
        return None
    
    token = credentials.credentials
    print(f"🔍 Token kontrolü: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            print("❌ Token'da user_id yok")
            return None
    except JWTError as e:
        print(f"❌ Token decode hatası: {e}")
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        print(f"✅ Kullanıcı bulundu: {user.email} (ID: {user.id})")
    else:
        print(f"❌ Kullanıcı bulunamadı: ID {user_id}")
    
    return user

# app/auth.py - En sona ekleyin

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Token varsa kullanıcıyı döndür, yoksa None döndür.
    Upload gibi opsiyonel token gerektiren endpoint'ler için.
    """
    if not credentials:
        print("⚠️ Token yok, anonim kullanıcı olarak devam")
        return None
    
    token = credentials.credentials
    print(f"🔍 Token kontrolü: {token[:20]}...")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            print("❌ Token'da user_id yok")
            return None
    except JWTError as e:
        print(f"❌ Token decode hatası: {e}")
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        print(f"✅ Kullanıcı bulundu: {user.email} (ID: {user.id})")
    else:
        print(f"❌ Kullanıcı bulunamadı: ID {user_id}")
    
    return user