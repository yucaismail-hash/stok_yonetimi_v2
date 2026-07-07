from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.api.endpoints import notifications, tasks, upload, forecast, simulate, report, pattern, safety_stock, backtest, supplier, learning, export, payment, profile, sectors, cost
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


# Router'ları ekle
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


@app.get("/")
def root():
    return {"message": "Stok Yönetim Sistemi v2 API"}

# app/main.py - En altına ekleyin

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        timeout_keep_alive=120,  # ✅ 120 saniye (varsayılan 5 saniye)
        timeout_graceful_shutdown=30
    )