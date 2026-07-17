from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import os
import requests
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult, Notification
from app.analysis.forecast import DemandForecaster
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.api.endpoints.upload import get_user_upload_data
from datetime import datetime, timedelta
import numpy as np

router = APIRouter()

# Pattern analizci ile forecast'u zenginleştir
pattern_analyzer = AdvancedDemandAnalyzer()
forecaster = DemandForecaster(seasonal_periods=52)
forecaster.set_pattern_analyzer(pattern_analyzer)


class ForecastRequest(BaseModel):
    horizon: int = 13
    model_type: str = "auto"


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
    db.query(AnalysisResult).filter(
        AnalysisResult.task_id == task_id
    ).update({
        'status': status,
        'message': message,
        'updated_at': datetime.utcnow()
    })
    db.commit()


# ============================================================
# 📌 SENKRON FORECAST
# ============================================================

@router.post("/forecast/batch")
def batch_forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu forecast analizi - Pattern ile zenginleştirilmiş
    Token maliyeti: 8 token
    """
    try:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
        file_name = cached_data.get('file_name')
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        results = []
        for material in materials:
            try:
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                # ✅ Pattern analizi
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(historical)
                
                # ✅ Pattern ile zenginleştirilmiş forecast
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                # Model karşılaştırması
                model_comparison = {}
                for model_name in ['holt_winters', 'arima', 'simple']:
                    try:
                        if model_name == 'holt_winters' and len(historical) >= 12:
                            model_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        elif model_name == 'arima' and len(historical) >= 8:
                            model_result = forecaster.arima_forecast(historical, request.horizon)
                        else:
                            model_result = forecaster.simple_forecast(historical, request.horizon)
                        
                        rmse = forecaster.calculate_model_rmse(historical, model_result.get('mean', []))
                        model_comparison[model_name] = {
                            'rmse': rmse,
                            'forecast': model_result.get('mean', [])
                        }
                    except:
                        pass
                
                outlier_info = forecaster.detect_outliers(historical)
                
                trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                
                # ✅ Pattern bilgilerini model_params'e ekle
                model_params = {}
                if forecast_result.get('model_used') == 'holt_winters':
                    model_params = {
                        'seasonal_periods': 52,
                        'trend': 'add',
                        'seasonal': 'add'
                    }
                elif forecast_result.get('model_used') == 'arima':
                    model_params = {
                        'order': '(1,1,1)',
                        'seasonal_order': None
                    }
                elif forecast_result.get('model_used') == 'simple':
                    model_params = {
                        'window': 4,
                        'weighted': True
                    }
                
                if 'selection_info' in forecast_result:
                    model_params.update(forecast_result['selection_info'])
                
                # ✅ Pattern bilgilerini ekle
                model_params['pattern'] = pattern
                model_params['pattern_label'] = get_pattern_label(pattern)
                model_params['pattern_color'] = get_pattern_color(pattern)
                model_params['cv'] = round(pattern_stats.get('cv', 0), 4)
                model_params['zero_ratio'] = round(pattern_stats.get('zero_ratio', 0), 4)
                
                selection_reason = forecast_result.get('selection_info', {}).get('selection_reason', 'Otomatik seçim')
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': request.horizon,
                    'selected_model': forecast_result.get('model_used', 'simple'),
                    'best_model_label': forecast_result.get('model_used', 'simple').replace('_', ' ').title(),
                    'model_description': f"{forecast_result.get('model_used', 'simple')} modeli kullanıldı",
                    'selection_reason': selection_reason,
                    'forecast': forecast_result.get('mean', []),
                    'lower_80': forecast_result.get('lower_80', []),
                    'upper_80': forecast_result.get('upper_80', []),
                    'lower_95': forecast_result.get('lower_95', []),
                    'upper_95': forecast_result.get('upper_95', []),
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': forecaster.calculate_model_rmse(historical, forecast_result.get('mean', [])),
                    'model_comparison': model_comparison,
                    'model_params': model_params,
                    'outlier_info': outlier_info,
                    'historical_data': historical,
                    'pattern': pattern,
                    'pattern_label': get_pattern_label(pattern),
                    'pattern_color': get_pattern_color(pattern),
                    'cv': round(pattern_stats.get('cv', 0), 4),
                    'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4)
                })
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir malzeme için tahmin yapılamadı!")
        
        # ============================================================
        # 📌 TEK KAYIT: analysis_results (Senkron - task_id NULL)
        # ============================================================
        
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'horizon': request.horizon,
            'model_type': request.model_type,
            'pattern_analysis': True
        }
        
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='forecast_batch',
            data=result_data,
            params={
                'horizon': request.horizon,
                'model_type': request.model_type,
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
                    'material_code': r.get('material_code'),
                    'group': r.get('group'),
                    'pattern': r.get('pattern'),
                    'cv': r.get('cv'),
                    'zero_ratio': r.get('zero_ratio'),
                    'trend': r.get('trend_direction'),
                }
                for r in results
            ]
            update_learning_from_pattern(current_user.id, pattern_results, db)
        
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 8,
            'result_id': analysis_result.id,
            'pattern_analysis': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC FORECAST
# ============================================================

@router.post("/forecast/batch/async")
def start_async_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Async forecast - Pattern ile zenginleştirilmiş"""
    
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
    
    upload_id = cached_data.get('upload_id')
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    task_id = str(uuid.uuid4())
    
    # ============================================================
    # 📌 TEK KAYIT: analysis_results (Async - task_id dolu)
    # ============================================================
    
    initial_data = {
        'status': 'processing',
        'message': 'Forecast analizi başlatıldı...',
        'total': len(materials),
        'results': [],
        'horizon': request.horizon,
        'model_type': request.model_type,
        'task_id': task_id,
        'pattern_analysis': True,
        'started_at': datetime.utcnow().isoformat()
    }
    
    initial_record = AnalysisResult(
        user_id=current_user.id,
        upload_id=upload_id,
        result_type='forecast_batch_async',
        data=initial_data,
        params={
            'horizon': request.horizon,
            'model_type': request.model_type,
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
        run_async_forecast_job,
        task_id=task_id,
        user_id=current_user.id,
        upload_id=upload_id,
        request=request,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Forecast analizi arka planda başlatıldı.",
        "token_cost": 8
    }


# ============================================================
# 📌 ASYNC FORECAST JOB
# ============================================================

def run_async_forecast_job(task_id: str, user_id: int, upload_id: str, request: ForecastRequest, db: Session):
    """Async forecast işini gerçekleştirir."""
    try:
        print(f"🔄 Async forecast başladı: Task ID {task_id}")
        
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
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                # ✅ Pattern analizi
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(historical)
                
                # ✅ Pattern ile zenginleştirilmiş forecast
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                # Model karşılaştırması
                model_comparison = {}
                for model_name in ['holt_winters', 'arima', 'simple']:
                    try:
                        if model_name == 'holt_winters' and len(historical) >= 12:
                            model_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        elif model_name == 'arima' and len(historical) >= 8:
                            model_result = forecaster.arima_forecast(historical, request.horizon)
                        else:
                            model_result = forecaster.simple_forecast(historical, request.horizon)
                        
                        rmse = forecaster.calculate_model_rmse(historical, model_result.get('mean', []))
                        model_comparison[model_name] = {
                            'rmse': rmse,
                            'forecast': model_result.get('mean', [])
                        }
                    except:
                        pass
                
                outlier_info = forecaster.detect_outliers(historical)
                
                trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                
                # ✅ Pattern bilgilerini model_params'e ekle
                model_params = {}
                if forecast_result.get('model_used') == 'holt_winters':
                    model_params = {
                        'seasonal_periods': 52,
                        'trend': 'add',
                        'seasonal': 'add'
                    }
                elif forecast_result.get('model_used') == 'arima':
                    model_params = {
                        'order': '(1,1,1)',
                        'seasonal_order': None
                    }
                elif forecast_result.get('model_used') == 'simple':
                    model_params = {
                        'window': 4,
                        'weighted': True
                    }
                
                if 'selection_info' in forecast_result:
                    model_params.update(forecast_result['selection_info'])
                
                # ✅ Pattern bilgilerini ekle
                model_params['pattern'] = pattern
                model_params['pattern_label'] = get_pattern_label(pattern)
                model_params['pattern_color'] = get_pattern_color(pattern)
                model_params['cv'] = round(pattern_stats.get('cv', 0), 4)
                model_params['zero_ratio'] = round(pattern_stats.get('zero_ratio', 0), 4)
                
                selection_reason = forecast_result.get('selection_info', {}).get('selection_reason', 'Otomatik seçim')
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': request.horizon,
                    'selected_model': forecast_result.get('model_used', 'simple'),
                    'best_model_label': forecast_result.get('model_used', 'simple').replace('_', ' ').title(),
                    'model_description': f"{forecast_result.get('model_used', 'simple')} modeli kullanıldı",
                    'selection_reason': selection_reason,
                    'forecast': forecast_result.get('mean', []),
                    'lower_80': forecast_result.get('lower_80', []),
                    'upper_80': forecast_result.get('upper_80', []),
                    'lower_95': forecast_result.get('lower_95', []),
                    'upper_95': forecast_result.get('upper_95', []),
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': forecaster.calculate_model_rmse(historical, forecast_result.get('mean', [])),
                    'model_comparison': model_comparison,
                    'model_params': model_params,
                    'outlier_info': outlier_info,
                    'historical_data': historical,
                    'pattern': pattern,
                    'pattern_label': get_pattern_label(pattern),
                    'pattern_color': get_pattern_color(pattern),
                    'cv': round(pattern_stats.get('cv', 0), 4),
                    'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4)
                })
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası (Task {task_id}): {e}")
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
            'horizon': request.horizon,
            'model_type': request.model_type,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Forecast analizi tamamlandı!',
            'pattern_analysis': True,
            'completed_at': datetime.utcnow().isoformat()
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
                    'material_code': r.get('material_code'),
                    'group': r.get('group'),
                    'pattern': r.get('pattern'),
                    'cv': r.get('cv'),
                    'zero_ratio': r.get('zero_ratio'),
                    'trend': r.get('trend_direction'),
                }
                for r in results
            ]
            update_learning_from_pattern(user_id, pattern_results, db)
        
        db.commit()
        
        # ============================================================
        # 📌 BİLDİRİM OLUŞTUR
        # ============================================================
        
        try:
            notification = Notification(
                user_id=user_id,
                title=f"✅ Talep Tahmini Tamamlandı!",
                message=f"Forecast raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
                type="success",
                link="/tasks"
            )
            db.add(notification)
            db.commit()
        except Exception as e:
            print(f"⚠️ Bildirim hatası: {e}")
        
        print(f"✅ Async forecast tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async forecast hatası (Task {task_id}): {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()