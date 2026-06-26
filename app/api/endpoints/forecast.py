from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult, UserAnalysisResult
from app.analysis.forecast import DemandForecaster
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.api.endpoints.upload import get_user_upload_data
from datetime import datetime, timedelta
import numpy as np

router = APIRouter()

# ✅ Pattern analizci ile forecast'u zenginleştir
pattern_analyzer = AdvancedDemandAnalyzer()
forecaster = DemandForecaster(seasonal_periods=52)
forecaster.set_pattern_analyzer(pattern_analyzer)


class ForecastRequest(BaseModel):
    horizon: int = 13
    model_type: str = "auto"


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
                    'historical_data': historical
                })
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir malzeme için tahmin yapılamadı!")
        
        from app.models import UserAnalysisResult
        
        result_data = {
            'total': len(results),
            'results': results,
            'horizon': request.horizon,
            'model_type': request.model_type,
            'pattern_analysis': True
        }
        
        for result in results:
            analysis_result = UserAnalysisResult(
                user_id=current_user.id,
                result_type='forecast_batch',
                material_code=result['material_code'],
                material_group=result.get('group', 'GENEL'),
                result_data=result_data,
                params={
                    'horizon': request.horizon,
                    'model_type': request.model_type,
                    'total_materials': len(results),
                    'pattern_analysis': True
                },
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 8,
            'pattern_analysis': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    task_id = str(uuid.uuid4())
    
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
        result_type='forecast_batch_async',
        data=initial_data,
        task_id=task_id
    )
    db.add(initial_record)
    db.commit()
    
    background_tasks.add_task(
        run_async_forecast_job,
        task_id=task_id,
        user_id=current_user.id,
        request=request,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Forecast analizi arka planda başlatıldı.",
        "token_cost": 8
    }


def run_async_forecast_job(task_id: str, user_id: int, request: ForecastRequest, db: Session):
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
                    'historical_data': historical
                })
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası (Task {task_id}): {e}")
                continue
        
        if not results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
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
        ).update({'data': result_data})
        
        from app.models import UserAnalysisResult
        
        for result in results:
            analysis_result = UserAnalysisResult(
                user_id=user_id,
                result_type='forecast_batch',
                material_code=result['material_code'],
                material_group=result.get('group', 'GENEL'),
                result_data={
                    'total': len(results),
                    'results': results,
                    'horizon': request.horizon,
                    'model_type': request.model_type,
                    'pattern_analysis': True
                },
                params={
                    'horizon': request.horizon,
                    'model_type': request.model_type,
                    'total_materials': len(results),
                    'task_id': task_id,
                    'pattern_analysis': True
                },
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
        db.commit()
        
        print(f"✅ Async forecast tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async forecast hatası (Task {task_id}): {e}")
        update_async_task_status(db, task_id, 'failed', str(e))


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
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['status'] = status
        data['message'] = message
        result.data = data
        db.commit()