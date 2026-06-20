from app.database import engine
from sqlalchemy import text

def update_database():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS company_name VARCHAR"))
            conn.execute(text("ALTER TABLE sectors ADD COLUMN IF NOT EXISTS description VARCHAR"))
            conn.execute(text("ALTER TABLE sectors ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW()"))
            conn.commit()
            print("✅ Veritabanı güncellendi")
        except Exception as e:
            print(f"⚠️ Veritabanı güncelleme hatası: {e}")

# app.main başlangıcında çağır
update_database()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.api.endpoints import upload, forecast, simulate, report, pattern, safety_stock, backtest, supplier, learning, export, payment, profile, sectors
from app.auth import auth_router
from app.admin import router as admin_router
from app.models import User, TokenCost, TokenHistory
from app.database import SessionLocal
from jose import jwt
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stok Yönetim Sistemi v2", version="0.1.0")


@app.middleware("http")
async def token_middleware(request: Request, call_next):
    # Admin, auth, docs, sectors endpoint'lerini muaf tut
    if request.url.path.startswith("/admin") or request.url.path.startswith("/auth") or request.url.path.startswith("/docs") or request.url.path.startswith("/openapi.json") or request.url.path.startswith("/api/sectors"):
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
        
        print(f"🔍 Endpoint: {endpoint_path}, Method: {method}")
        
        # Sadece /api/ ile başlayan endpoint'ler için token kontrolü yap
        if endpoint_path.startswith("/api/"):
            token_cost = db.query(TokenCost).filter(
                TokenCost.endpoint == endpoint_path,
                TokenCost.method == method,
                TokenCost.is_active == True
            ).first()
            
            if token_cost:
                if user.token_balance < token_cost.cost:
                    return JSONResponse(
                        status_code=402,
                        content={"detail": f"Yetersiz token. Gerekli: {token_cost.cost}, Mevcut: {user.token_balance}"}
                    )
                
                user.token_balance -= token_cost.cost
                
                history = TokenHistory(
                    user_id=user.id,
                    endpoint=endpoint_path,
                    cost=token_cost.cost,
                    balance_after=user.token_balance
                )
                db.add(history)
                db.commit()
                
                print(f"✅ Token harcandı: {token_cost.cost}, Kalan: {user.token_balance}")
            else:
                print(f"⚠️ Token cost bulunamadı: {endpoint_path}")
        
        request.state.user_id = user_id
        request.state.user = user
        
        response = await call_next(request)
        return response
    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://stok-yonetimi-frontend.onrender.com",
        "https://*.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Base.metadata.create_all(bind=engine)


app.include_router(auth_router, prefix="/auth", tags=["authentication"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(sectors.router, prefix="/api", tags=["sectors"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(forecast.router, prefix="/api", tags=["forecast"])
app.include_router(simulate.router, prefix="/api", tags=["simulate"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(pattern.router, prefix="/api", tags=["pattern"])
app.include_router(safety_stock.router, prefix="/api", tags=["safety_stock"])
app.include_router(backtest.router, prefix="/api", tags=["backtest"])
app.include_router(supplier.router, prefix="/api", tags=["supplier"])
app.include_router(learning.router, prefix="/api", tags=["learning"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(payment.router, prefix="/api", tags=["payment"])
app.include_router(profile.router, prefix="/api", tags=["profile"])


@app.get("/")
def root():
    return {"message": "Stok Yönetim Sistemi v2 API"}