from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data

router = APIRouter()
optimizer = ComprehensiveSafetyStockOptimizer()


@router.post("/safety-stock/batch")
def calculate_safety_stock_batch(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Safety Stock analizi - Cache'ten verileri alır.
    Token maliyeti: 10 token
    """
    try:
        # 1. Cache'ten verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        service_level = request.get('service_level', 0.95)
        
        # 2. Analiz
        results = []
        for material in materials:
            weekly_data = material.get('historical_demand', [])
            lead_time = material.get('lead_time_days', 14)
            
            if len(weekly_data) < 4:
                continue
            
            ss_result = optimizer.calculate_all_methods(
                weekly_data,
                lead_time,
                service_level
            )
            
            results.append({
                'material_code': material.get('code', ''),
                'group': material.get('group', 'GENEL'),
                'lead_time_days': lead_time,
                'classic_ss': ss_result.get('classic_ss', 0),
                'croston_ss': ss_result.get('croston_ss', 0),
                'syntetos_boylan_ss': ss_result.get('syntetos_boylan_ss', 0),
                'bootstrapping_ss': ss_result.get('bootstrapping_ss', 0),
                'ml_ss': ss_result.get('ml_ss', 0),
                'hybrid_ss': ss_result.get('hybrid_ss', 0)
            })
        
        # 3. Sonuçları kaydet
        if results:
            from app.models import UserAnalysisResult
            
            for result in results:
                analysis_result = UserAnalysisResult(
                    user_id=current_user.id,
                    result_type='safety_stock_batch',
                    material_code=result['material_code'],
                    material_group=result.get('group', 'GENEL'),
                    result_data=result,
                    params={'service_level': service_level, 'total_materials': len(results)},
                    expires_at=datetime.utcnow() + timedelta(days=15)
                )
                db.add(analysis_result)
            db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 10
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))