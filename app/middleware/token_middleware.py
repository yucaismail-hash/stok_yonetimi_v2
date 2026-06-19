from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from app.models import User, TokenCost, TokenHistory
from app.database import SessionLocal
from jose import jwt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")

@app.middleware("http")
async def token_middleware(request: Request, call_next):
    # Admin, auth, docs endpoint'lerini muaf tut
    if request.url.path.startswith("/admin") or request.url.path.startswith("/auth") or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json"):
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return await call_next(request)
    
    token = auth_header.replace("Bearer ", "")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
    except:
        return await call_next(request)
    
    if not user_id:
        return await call_next(request)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return await call_next(request)
        
        endpoint_path = request.url.path
        method = request.method
        
        # Token cost'u bul
        token_cost = db.query(TokenCost).filter(
            TokenCost.endpoint == endpoint_path,
            TokenCost.method == method,
            TokenCost.is_active == True
        ).first()
        
        # ZORLA TOKEN DÜŞ (TEST)
        if user.token_balance > 0:
            user.token_balance -= 1
            db.commit()
            print(f"🔥 TEST: 1 token harcandı! Yeni bakiye: {user.token_balance}")
        else:
            print(f"⚠️ Token cost bulunamadı: {endpoint_path}, token harcanmadı")
        
        # Kullanıcı bilgisini request.state'e ekle
        request.state.user_id = user_id
        request.state.user = user
        
        response = await call_next(request)
        return response
    finally:
        db.close()