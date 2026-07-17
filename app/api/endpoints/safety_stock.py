from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.models import User, AnalysisResult, AnalysisBatchResult, AnalysisMaterialSummary, Notification
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
    Token maliyeti: 4 token
    """
    try:
        token_cost = 4
        if current_user.token_balance < token_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Yetersiz kredi! Gerekli: {token_cost}, Mevcut: {current_user.token_balance}"
            )
        
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
        file_name = cached_data.get('file_name')
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        service_level = request.get('service_level', 0.95)
        
        results = []
        for material in materials:
            weekly_data = material.get('historical_demand', [])
            lead_time = material.get('lead_time_days', 14)
            
            if len(weekly_data) < 4:
                continue
            
            pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
            ss_result = optimizer.calculate_all_methods(
                weekly_data,
                lead_time,
                service_level
            )
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
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir sonuç üretilemedi!")
        
        # ============================================================
        # 📌 TEK KAYIT: analysis_results (Senkron - task_id NULL)
        # ============================================================
        
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'service_level': service_level,
            'pattern_analysis': True
        }
        
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='safety_stock_batch',
            data=result_data,
            params={
                'service_level': service_level,
                'total_materials': len(results),
                'pattern_analysis': True
            },
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(analysis_result)
        
        # Öğrenme verilerini güncelle
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
        
        current_user.token_balance -= token_cost
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': token_cost,
            'new_balance': current_user.token_balance,
            'result_id': analysis_result.id,
            'pattern_analysis': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
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
    
    token_cost = 6
    if current_user.token_balance < token_cost:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Yetersiz kredi! Gerekli: {token_cost}, Mevcut: {current_user.token_balance}"
        )
    
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
    
    upload_id = cached_data.get('upload_id')
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    service_level = request.get('service_level', 0.95)
    task_id = str(uuid.uuid4())
    
    current_user.token_balance -= token_cost
    db.commit()
    
    # ============================================================
    # 📌 TEK KAYIT: analysis_results (Async - task_id dolu)
    # ============================================================
    
    initial_data = {
        'status': 'processing',
        'message': 'Safety Stock analizi başlatıldı, işleniyor...',
        'total': len(materials),
        'results': [],
        'service_level': service_level,
        'task_id': task_id,
        'pattern_analysis': True,
        'started_at': datetime.utcnow().isoformat(),
        'token_cost': token_cost,
    }
    
    initial_record = AnalysisResult(
        user_id=current_user.id,
        upload_id=upload_id,
        result_type='safety_stock_batch_async',
        data=initial_data,
        params={
            'service_level': service_level,
            'total_materials': len(materials),
            'pattern_analysis': True
        },
        total_materials=len(materials),
        task_id=task_id,
        status='processing',
        progress=0,
        message='Başlatıldı...',
        expires_at=datetime.utcnow() + timedelta(days=15)
    )
    db.add(initial_record)
    db.commit()
    
    background_tasks.add_task(
        run_async_safety_stock_job,
        task_id=task_id,
        user_id=current_user.id,
        upload_id=upload_id,
        service_level=service_level,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Safety Stock analizi arka planda başlatıldı.",
        "token_cost": token_cost,
        "new_balance": current_user.token_balance
    }


def run_async_safety_stock_job(task_id: str, user_id: int, upload_id: str, service_level: float, db: Session):
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
                
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
                ss_result = optimizer.calculate_all_methods(
                    weekly_data,
                    lead_time,
                    service_level
                )
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
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Safety Stock hatası ({material.get('code', '')}): {e}")
                continue
        
        if not results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
        # ============================================================
        # 📌 AYNI KAYDI GÜNCELLE (analysis_results)
        # ============================================================
        
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'service_level': service_level,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Safety Stock analizi tamamlandı!',
            'pattern_analysis': True,
            'completed_at': datetime.utcnow().isoformat(),
            'token_cost': 6,
        }
        
        db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).update({
            'data': result_data,
            'status': 'completed',
            'progress': 100,
            'message': 'Tamamlandı!',
            'total_materials': len(results),
            'updated_at': datetime.utcnow()
        })
        
        # Öğrenme verilerini güncelle
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
        
        db.commit()
        
        # Bildirim oluştur
        try:
            notification = Notification(
                user_id=user_id,
                title=f"✅ Emniyet Stoğu Analizi Tamamlandı!",
                message=f"Safety Stock raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
                type="success",
                link="/tasks"
            )
            db.add(notification)
            db.commit()
        except Exception as e:
            print(f"⚠️ Bildirim hatası: {e}")
        
        print(f"✅ Async safety stock tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async safety stock hatası: {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()

# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
# ============================================================

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


def get_recommended_method(pattern: str, pattern_stats: Dict) -> str:
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