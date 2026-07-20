from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base, init_db
from app.api.endpoints import notifications, tasks, upload, forecast, simulate, report, pattern, safety_stock, backtest, supplier, learning, export, payment, profile, sectors, cost
from app.api.endpoints import polar, dashboard  
from app.auth import auth_router
from app.admin import router as admin_router
from app.models import User, TokenCost, TokenHistory
from app.database import SessionLocal
from jose import jwt
import os
import logging
import re
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Stok Yönetim Sistemi v2", version="0.1.0")


# ============================================
# Uygulama Başlangıç Olayı
# ============================================

@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında sadece tabloları oluştur."""
    logger.info("🚀 Starting up...")
    init_db()
    logger.info("✅ Database tables ready")
    logger.info("ℹ️  Run /admin/token-costs/init-defaults to initialize token costs")
    logger.info("ℹ️  Run /admin/credit-packages/init-defaults to initialize credit packages")


# ============================================
# Token Middleware
# ============================================

@app.middleware("http")
async def token_middleware(request: Request, call_next):
    # ✅ Muaf tutulacak endpoint'ler
    exempt_patterns = [
        r"^/admin",
        r"^/auth", 
        r"^/docs",
        r"^/openapi.json",
        r"^/api/sectors",
        r"^/api/cost",
        r"^/api/upload",
        r"^/api/upload/status",
        r"^/api/upload/upload",
        r"^/api/upload/clear",
        r"^/api/upload/results",
        r"^/api/polar/webhook",
        r"^/success$",        # ✅ Public
        r"^/cancel$",         # ✅ Public
    ]
    
    path = request.url.path
    
    # Endpoint muaf mı kontrol et
    for pattern in exempt_patterns:
        if re.match(pattern, path):
            print(f"⏩ Muaf endpoint: {path}")
            return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        print(f"❌ Token yok: {path}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Authorization header required"}
        )
    
    token = auth_header.replace("Bearer ", "")
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token payload"}
            )
    except Exception as e:
        print(f"❌ Token geçersiz: {e}")
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(
                status_code=401,
                content={"detail": "User not found"}
            )
        
        endpoint_path = request.url.path
        method = request.method
        
        print(f"🔍 Endpoint: {endpoint_path}, Method: {method}")
        
        # ✅ Token cost kontrolü - Dinamik path eşleştirme
        if endpoint_path.startswith("/api/"):
            token_cost = None
            
            # 1. Önce tam eşleşme kontrol et
            token_cost = db.query(TokenCost).filter(
                TokenCost.endpoint == endpoint_path,
                TokenCost.method == method,
                TokenCost.is_active == True
            ).first()
            
            # 2. Tam eşleşme yoksa dinamik pattern kontrolü
            if not token_cost:
                # ✅ Async status için pattern
                if "/async/status/" in endpoint_path:
                    token_cost = db.query(TokenCost).filter(
                        TokenCost.endpoint == "/api/forecast/async/status/{task_id}",
                        TokenCost.method == method,
                        TokenCost.is_active == True
                    ).first()
                    if token_cost:
                        print(f"✅ Pattern eşleşti: /api/forecast/async/status/{{task_id}}")
                
                # ✅ Async result için pattern
                elif "/async/result/" in endpoint_path:
                    token_cost = db.query(TokenCost).filter(
                        TokenCost.endpoint == "/api/forecast/async/result/{task_id}",
                        TokenCost.method == method,
                        TokenCost.is_active == True
                    ).first()
                    if token_cost:
                        print(f"✅ Pattern eşleşti: /api/forecast/async/result/{{task_id}}")
            
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


# ============================================
# CORS Ayarları
# ============================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://stok-yonetimi-frontend.onrender.com",
        "https://*.onrender.com",
        "https://www.stokonomi.com", 
        "https://stokonomi.com"   
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Router'ları Ekle
# ============================================

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
app.include_router(cost.router, prefix="/api", tags=["cost"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(notifications.router, prefix="/api", tags=["notifications"])
app.include_router(polar.router, prefix="/api", tags=["polar"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])


# ============================================
# Public Endpoint'ler (Success / Cancel)
# ============================================

# ✅ Success endpoint'i - Ödeme başarılı
@app.get("/success")
async def success_page(request: Request):
    checkout_id = request.query_params.get("checkout_id")
    return {
        "message": "Ödeme başarıyla tamamlandı!",
        "status": "success",
        "checkout_id": checkout_id
    }

# ✅ Cancel endpoint'i - Ödeme iptal
@app.get("/cancel")
async def cancel_page(request: Request):
    checkout_id = request.query_params.get("checkout_id")
    return {
        "message": "Ödeme iptal edildi.",
        "status": "canceled",
        "checkout_id": checkout_id
    }


# ============================================
# Root Endpoint
# ============================================

@app.get("/")
def root():
    return {"message": "Stok Yönetim Sistemi v2 API"}


# ============================================
# Uygulama Çalıştırma
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=120,
        timeout_graceful_shutdown=60
    )