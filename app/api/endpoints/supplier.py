import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from app.analysis.supplier import (
    SupplierPerformanceAnalyzer, 
    SupplierShareOptimizer, 
    calculate_tail_risk_from_simulation, 
    calculate_cvar_95, 
    calculate_service_level_gap
)

router = APIRouter()

# Global analyzer instance
supplier_analyzer = SupplierPerformanceAnalyzer()
share_optimizer = SupplierShareOptimizer(supplier_analyzer)

# ==================== REQUEST MODELS ====================
class DeliveryRecordRequest(BaseModel):
    supplier_id: str
    planned_date: str  # ISO format
    actual_date: str
    planned_qty: float
    actual_qty: float
    defects: int = 0


class SupplierShareRequest(BaseModel):
    material_code: str
    suppliers: List[Dict]  # [{"supplier_id": "SUP001", "share": 0.6, "unit_cost": 100}, ...]
    current_share_map: Dict[str, float]
    delta_min: float = 0.02
    delta_max: float = 0.15
    delta_step: float = 0.01
    min_share: float = 0.10
    max_share: float = 0.90


class SupplierRiskRequest(BaseModel):
    supplier_id: str
    delivery_history: Optional[List[Dict]] = None


class TailRiskRequest(BaseModel):
    shortage_paths: List[List[float]]
    service_level: float = 0.95


class CVaRRequest(BaseModel):
    shortage_paths: List[List[float]]


class ServiceLevelGapRequest(BaseModel):
    actual_service_level: float
    target_service_level: float = 0.95


# ==================== ENDPOINTS ====================
@router.post("/supplier/delivery")
def add_delivery_record(request: DeliveryRecordRequest):
    """Tedarikçi teslimat kaydı ekle"""
    try:
        planned_date = datetime.fromisoformat(request.planned_date)
        actual_date = datetime.fromisoformat(request.actual_date)
        
        supplier_analyzer.add_delivery_record(
            request.supplier_id,
            planned_date,
            actual_date,
            request.planned_qty,
            request.actual_qty,
            request.defects
        )
        return {"status": "success", "message": "Teslimat kaydı eklendi"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/supplier/{supplier_id}/risk")
def get_supplier_risk(supplier_id: str):
    """Tedarikçi risk skorunu getir"""
    try:
        risk_score = supplier_analyzer.get_supplier_risk_score(supplier_id)
        perf_score = supplier_analyzer.get_supplier_performance_score(supplier_id)
        
        return {
            "supplier_id": supplier_id,
            "risk_score": risk_score,
            "performance_score": perf_score,
            "risk_level": "YÜKSEK" if risk_score > 0.7 else ("ORTA" if risk_score > 0.4 else "DÜŞÜK"),
            "performance_level": "İYİ" if perf_score > 0.7 else ("ORTA" if perf_score > 0.4 else "KÖTÜ")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/supplier/optimize-shares")
def optimize_supplier_shares(request: SupplierShareRequest):
    """En düşük maliyetli tedarikçi paylarını optimize et"""
    try:
        # Aday pay kombinasyonlarını oluştur
        candidates = share_optimizer.generate_candidates(
            suppliers=request.suppliers,
            current_share_map=request.current_share_map,
            delta_min=request.delta_min,
            delta_max=request.delta_max,
            delta_step=request.delta_step,
            min_share=request.min_share,
            max_share=request.max_share
        )
        
        # Her adayın maliyetini hesapla (basitleştirilmiş)
        results = []
        for cand in candidates[:10]:  # İlk 10 adayı değerlendir
            weighted_factor = share_optimizer.calculate_weighted_supplier_factor(
                [{"supplier_id": k, "share": v} for k, v in cand.items()]
            )
            weighted_risk = share_optimizer.calculate_weighted_risk_score(
                [{"supplier_id": k, "share": v} for k, v in cand.items()]
            )
            results.append({
                "shares": cand,
                "weighted_factor": round(weighted_factor, 3),
                "weighted_risk": round(weighted_risk, 3),
                "score": round(weighted_factor * (1 - weighted_risk), 3)
            })
        
        # En iyi skoru bul
        best = max(results, key=lambda x: x["score"])
        
        return {
            "best_shares": best["shares"],
            "weighted_factor": best["weighted_factor"],
            "weighted_risk": best["weighted_risk"],
            "score": best["score"],
            "all_candidates": results,
            "recommendation": "Önerilen pay dağılımı best_shares içindedir"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/supplier/weighted-factor")
def calculate_weighted_factor(suppliers: List[Dict]):
    """Ağırlıklı tedarikçi faktörünü hesapla"""
    try:
        weighted_factor = share_optimizer.calculate_weighted_supplier_factor(suppliers)
        return {"weighted_supplier_factor": round(weighted_factor, 3)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/supplier/lead-time-distribution")
def get_lead_time_distribution(supplier_id: str, demand_level: Optional[str] = None):
    """Tedarikçi lead time dağılımını getir"""
    try:
        result = supplier_analyzer.get_supplier_lead_time_distribution(supplier_id, demand_level)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== RISK METRICS ENDPOINTS ====================
@router.post("/risk/tail-risk")
def calculate_tail_risk(request: TailRiskRequest):
    """Simülasyon sonuçlarından Tail Risk hesapla"""
    try:
        shortage_array = np.array(request.shortage_paths)
        tail_risk = calculate_tail_risk_from_simulation(shortage_array, request.service_level)
        return {
            "tail_risk": tail_risk,
            "service_level": request.service_level,
            "interpretation": "Yüksek" if tail_risk > 0.6 else ("Orta" if tail_risk > 0.3 else "Düşük")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risk/cvar95")
def calculate_cvar(request: CVaRRequest):
    """CVaR95 (Conditional Value at Risk) hesapla"""
    try:
        shortage_array = np.array(request.shortage_paths)
        cvar_95 = calculate_cvar_95(shortage_array)
        return {"cvar_95": cvar_95}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/risk/service-level-gap")
def calculate_gap(request: ServiceLevelGapRequest):
    """Servis seviyesi farkını hesapla"""
    try:
        result = calculate_service_level_gap(request.actual_service_level, request.target_service_level)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== INFO ENDPOINTS ====================
@router.get("/supplier/info")
def get_supplier_info():
    """Tedarikçi modülü hakkında bilgi verir"""
    return {
        "description": "Tedarikçi performans analizi, risk skoru, pay optimizasyonu",
        "endpoints": [
            "/supplier/delivery - POST - Teslimat kaydı ekle",
            "/supplier/{id}/risk - GET - Risk ve performans skoru",
            "/supplier/optimize-shares - POST - Pay optimizasyonu",
            "/supplier/weighted-factor - POST - Ağırlıklı faktör",
            "/supplier/lead-time-distribution - POST - LT dağılımı",
            "/risk/tail-risk - POST - Tail Risk hesapla",
            "/risk/cvar95 - POST - CVaR95 hesapla",
            "/risk/service-level-gap - POST - Servis farkı"
        ]
    }