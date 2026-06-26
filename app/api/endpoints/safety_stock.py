from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.models import User, AnalysisResult, UserAnalysisResult
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import uuid

router = APIRouter()
optimizer = ComprehensiveSafetyStockOptimizer()
pattern_analyzer = AdvancedDemandAnalyzer()


# ============================================================
# 📌 SENKRON SAFETY STOCK (PATTERN ENTEGRE)
# ============================================================
@router.post("/safety-stock/batch")
def calculate_safety_stock_batch(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Safety Stock analizi - Pattern bilgisi ile zenginleştirilmiş.
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
            
            # ✅ Pattern analizi
            pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
            
            # ✅ Safety Stock hesaplama
            ss_result = optimizer.calculate_all_methods(
                weekly_data,
                lead_time,
                service_level
            )
            
            # ✅ Pattern'e göre önerilen SS metodu
            recommended_method = get_recommended_method(pattern, pattern_stats)
            
            results.append({
                'material_code': material.get('code', ''),
                'group': material.get('group', 'GENEL'),
                'lead_time_days': lead_time,
                'pattern': pattern,
                'pattern_label': get_pattern_label(pattern),
                'pattern_color': get_pattern_color(pattern),
                'cv': round(pattern_stats.get('cv', 0), 4),
                'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4),
                'trend': round(pattern_stats.get('trend', 0), 2),
                'classic_ss': ss_result.get('classic_ss', 0),
                'croston_ss': ss_result.get('croston_ss', 0),
                'syntetos_boylan_ss': ss_result.get('syntetos_boylan_ss', 0),
                'bootstrapping_ss': ss_result.get('bootstrapping_ss', 0),
                'ml_ss': ss_result.get('ml_ss', 0),
                'hybrid_ss': ss_result.get('hybrid_ss', 0),
                'recommended_method': recommended_method,
                'recommended_method_label': get_method_label(recommended_method)
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
                    params={
                        'service_level': service_level,
                        'total_materials': len(results),
                        'pattern_analysis': True
                    },
                    expires_at=datetime.utcnow() + timedelta(days=15)
                )
                db.add(analysis_result)
            db.commit()
        
        # 4. Öğrenme verilerini güncelle
        if results:
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
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 10,
            'pattern_analysis': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC SAFETY STOCK (PATTERN ENTEGRE)
# ============================================================
@router.post("/safety-stock/batch/async")
def start_async_safety_stock(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Async safety stock analizi - Pattern ile zenginleştirilmiş."""
    
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
    
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    service_level = request.get('service_level', 0.95)
    task_id = str(uuid.uuid4())
    
    # ✅ Başlangıç kaydı
    initial_data = {
        'status': 'processing',
        'message': 'Safety Stock analizi başlatıldı, işleniyor...',
        'total': len(materials),
        'results': [],
        'service_level': service_level,
        'task_id': task_id,
        'pattern_analysis': True,
        'started_at': datetime.utcnow().isoformat()
    }
    
    initial_record = AnalysisResult(
        user_id=current_user.id,
        result_type='safety_stock_batch_async',
        data=initial_data,
        task_id=task_id
    )
    db.add(initial_record)
    db.commit()
    
    background_tasks.add_task(
        run_async_safety_stock_job,
        task_id=task_id,
        user_id=current_user.id,
        service_level=service_level,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Safety Stock analizi arka planda başlatıldı.",
        "token_cost": 10
    }


def run_async_safety_stock_job(task_id: str, user_id: int, service_level: float, db: Session):
    """Async safety stock işini gerçekleştirir."""
    try:
        print(f"🔄 Async safety stock analizi başladı: Task ID {task_id}")
        
        cached_data = get_user_upload_data(user_id)
        if not cached_data:
            update_async_task_status(db, task_id, 'failed', 'Veri bulunamadı')
            return
        
        materials = cached_data.get('materials', [])
        if not materials:
            update_async_task_status(db, task_id, 'failed', 'Malzeme bulunamadı')
            return
        
        results = []
        total = len(materials)
        
        for idx, material in enumerate(materials):
            try:
                weekly_data = material.get('historical_demand', [])
                lead_time = material.get('lead_time_days', 14)
                
                if len(weekly_data) < 4:
                    continue
                
                # ✅ Pattern analizi
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
                
                # ✅ Safety Stock hesaplama
                ss_result = optimizer.calculate_all_methods(
                    weekly_data,
                    lead_time,
                    service_level
                )
                
                # ✅ Pattern'e göre önerilen SS metodu
                recommended_method = get_recommended_method(pattern, pattern_stats)
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'lead_time_days': lead_time,
                    'pattern': pattern,
                    'pattern_label': get_pattern_label(pattern),
                    'pattern_color': get_pattern_color(pattern),
                    'cv': round(pattern_stats.get('cv', 0), 4),
                    'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4),
                    'trend': round(pattern_stats.get('trend', 0), 2),
                    'classic_ss': ss_result.get('classic_ss', 0),
                    'croston_ss': ss_result.get('croston_ss', 0),
                    'syntetos_boylan_ss': ss_result.get('syntetos_boylan_ss', 0),
                    'bootstrapping_ss': ss_result.get('bootstrapping_ss', 0),
                    'ml_ss': ss_result.get('ml_ss', 0),
                    'hybrid_ss': ss_result.get('hybrid_ss', 0),
                    'recommended_method': recommended_method,
                    'recommended_method_label': get_method_label(recommended_method)
                })
                
                # ✅ İlerleme güncelle
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Safety Stock hatası ({material.get('code', '')}): {e}")
                continue
        
        if not results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
        # ✅ 1. AnalysisResult'u güncelle (ASYNC görevler için)
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'service_level': service_level,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Safety Stock analizi tamamlandı!',
            'pattern_analysis': True,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).update({'data': result_data})
        
        # ✅ 2. UserAnalysisResult'a kaydet (Geçmiş için)
        from app.models import UserAnalysisResult
        
        for result in results:
            analysis_result = UserAnalysisResult(
                user_id=user_id,
                result_type='safety_stock_batch',
                material_code=result['material_code'],
                material_group=result.get('group', 'GENEL'),
                result_data=result,
                params={
                    'service_level': service_level,
                    'total_materials': len(results),
                    'task_id': task_id,
                    'pattern_analysis': True
                },
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
        db.commit()
        
        # 4. Öğrenme verilerini güncelle
        if results:
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
            update_learning_from_pattern(user_id, pattern_results, db)
        
        print(f"✅ Async safety stock tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async safety stock hatası: {e}")
        update_async_task_status(db, task_id, 'failed', str(e))


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
# ============================================================
def get_pattern_label(pattern: str) -> str:
    """Pattern label'ını döndür"""
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
    """Pattern renk kodu"""
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


def get_recommended_method(pattern: str, pattern_stats: Dict) -> str:
    """Pattern'e göre önerilen SS metodunu döndür"""
    cv = pattern_stats.get('cv', 0)
    zero_ratio = pattern_stats.get('zero_ratio', 0)
    
    if pattern == 'SIFIR_TALEP':
        return 'classic_ss'
    elif pattern in ['DUZENLI_SABIT', 'DUZENLI_ARTS', 'DUZENLI_AZALIS']:
        if cv < 0.2:
            return 'classic_ss'
        else:
            return 'hybrid_ss'
    elif pattern in ['ARALIKLI_DUSUK', 'ARALIKLI_YUKSEK']:
        if zero_ratio > 0.6:
            return 'croston_ss'
        else:
            return 'syntetos_boylan_ss'
    elif pattern in ['DEGISKEN', 'YUKSEK_DEGISKEN']:
        if cv < 0.5:
            return 'ml_ss'
        else:
            return 'bootstrapping_ss'
    elif pattern == 'ASIRI_DEGISKEN':
        return 'bootstrapping_ss'
    else:
        return 'hybrid_ss'


def get_method_label(method: str) -> str:
    """SS metodu label'ı"""
    labels = {
        'classic_ss': 'Klasik SS',
        'croston_ss': 'Croston',
        'syntetos_boylan_ss': 'Syntetos-Boylan',
        'bootstrapping_ss': 'Bootstrapping',
        'ml_ss': 'ML Tabanlı',
        'hybrid_ss': 'Hibrit (Önerilen)',
    }
    return labels.get(method, method)


def update_async_progress(db: Session, task_id: str, progress: int, message: str, completed: int):
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['progress'] = progress
        data['message'] = message
        data['completed_materials'] = completed
        result.data = data
        db.commit()


def update_async_task_status(db: Session, task_id: str, status: str, message: str):
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['status'] = status
        data['message'] = message
        result.data = data
        db.commit()