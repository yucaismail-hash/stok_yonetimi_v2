from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import json

router = APIRouter()
analyzer = AdvancedDemandAnalyzer()


@router.post("/pattern/batch")
def analyze_pattern_batch(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu pattern analizi - Yüklenen tüm malzemeler için pattern hesaplar.
    Token maliyeti: 5 token (middleware tarafından otomatik düşülür)
    """
    try:
        # 1. Cache'ten verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        # 2. Pattern analizi
        results = []
        for material in materials:
            weekly_data = material.get('historical_demand', [])
            if len(weekly_data) < 4:
                continue
            
            pattern, stats = analyzer.analyze_demand_pattern(weekly_data)
            results.append({
                'material_code': material.get('code', ''),
                'group': material.get('group', 'GENEL'),
                'pattern': pattern,
                'cv': stats['cv'],
                'zero_ratio': stats['zero_ratio'],
                'trend': stats['trend'],
                'mean': stats['mean'],
                'std': stats['std'],
                'median': stats['median']
            })
        
        # 3. Sonuçları kaydet (15 gün)
        from app.models import UserAnalysisResult

        # ✅ Analiz sonucu verisini hazırla
        result_data = {
            'total': len(results),
            'results': results
        }

        for result in results:
            analysis_result = UserAnalysisResult(
                user_id=current_user.id,
                result_type='pattern_batch',
                material_code=result['material_code'],
                material_group=result.get('group', 'GENEL'),
                result_data=result_data,  # ✅ Tüm veriyi kaydet
                params={'total_materials': len(results)},
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
        db.commit()
        
        # 4. Öğrenme verilerini güncelle
        from app.api.endpoints.learning import update_learning_from_pattern
        update_learning_from_pattern(current_user.id, results, db)
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))