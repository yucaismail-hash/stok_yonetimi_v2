from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.models import User, AnalysisResult
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data

router = APIRouter()
analyzer = AdvancedDemandAnalyzer()


def get_pattern_label(pattern: str) -> str:
    labels = {
        'DUZENLI_SABIT': 'Düzenli Sabit',
        'DUZENLI_ARTS': 'Düzenli Artan',
        'DUZENLI_AZALIS': 'Düzenli Azalan',
        'DEGISKEN': 'Değişken',
        'YUKSEK_DEGISKEN': 'Yüksek Değişken',
        'ASIRI_DEGISKEN': 'Aşırı Değişken',
        'SIFIR_TALEP': 'Sıfır Talep',
        'ARALIKLI_DUSUK': 'Aralıklı Düşük',
        'ARALIKLI_YUKSEK': 'Aralıklı Yüksek',
    }
    return labels.get(pattern, pattern)


def get_pattern_color(pattern: str) -> str:
    colors = {
        'DUZENLI_SABIT': 'success',
        'DUZENLI_ARTS': 'info',
        'DUZENLI_AZALIS': 'warning',
        'DEGISKEN': 'primary',
        'YUKSEK_DEGISKEN': 'secondary',
        'ASIRI_DEGISKEN': 'error',
        'SIFIR_TALEP': 'error',
        'ARALIKLI_DUSUK': 'info',
        'ARALIKLI_YUKSEK': 'warning',
    }
    return colors.get(pattern, 'default')


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
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
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
                'pattern_label': get_pattern_label(pattern),
                'pattern_color': get_pattern_color(pattern),
                'cv': stats['cv'],
                'zero_ratio': stats['zero_ratio'],
                'trend': stats['trend'],
                'mean': stats['mean'],
                'std': stats['std'],
                'median': stats['median']
            })
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir malzeme için pattern analizi yapılamadı!")
        
        # ============================================================
        # 📌 TEK KAYIT: analysis_results (Senkron - task_id NULL)
        # ============================================================
        
        result_data = {
            'total': len(results),
            'results': results
        }
        
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='pattern_batch',
            data=result_data,
            params={'total_materials': len(results)},
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(analysis_result)
        
        # Öğrenme verilerini güncelle
        from app.api.endpoints.learning import update_learning_from_pattern
        pattern_results = [
            {
                'material_code': r['material_code'],
                'group': r['group'],
                'pattern': r['pattern'],
                'cv': r['cv'],
                'zero_ratio': r['zero_ratio'],
                'trend': r['trend']
            }
            for r in results
        ]
        update_learning_from_pattern(current_user.id, pattern_results, db)
        
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 5,
            'result_id': analysis_result.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))