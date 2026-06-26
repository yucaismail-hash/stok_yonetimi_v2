from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult
from app.analysis.forecast import DemandForecaster
from app.auth import get_current_user
from app.api.endpoints.upload import get_user_upload_data
from datetime import datetime, timedelta
import numpy as np

router = APIRouter()
forecaster = DemandForecaster(seasonal_periods=52)


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
    Toplu forecast analizi - Yüklenen tüm malzemeler için talep tahmini yapar.
    Token maliyeti: 8 token (middleware tarafından otomatik düşülür)
    """
    try:
        # 1. Cache'ten verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        # 2. Forecast analizi
        results = []
        for material in materials:
            try:
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                # Ana tahmin
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                # ✅ MODEL KARŞILAŞTIRMASI - HER MODEL KENDİ TAHMİNİNİ YAPAR
                # 📌 MODEL KARŞILAŞTIRMASI - TÜM MODELLERİ DENE VE LOGLA
                model_comparison = {}

                print(f"📊 Malzeme: {material.get('code', '')} - Veri uzunluğu: {len(historical)} hafta")

                # 1. Holt-Winters
                try:
                    # ✅ Veri en az 8 hafta ise dene
                    if len(historical) >= 8:
                        print(f"🔄 HW deneniyor...")
                        hw_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        hw_forecast = hw_result.get('mean', [])
                        if hw_forecast and len(hw_forecast) > 0:
                            hw_rmse = forecaster.calculate_model_rmse(historical, hw_forecast)
                            model_comparison['holt_winters'] = {
                                'rmse': hw_rmse,
                                'forecast': hw_forecast
                            }
                            print(f"✅ HW RMSE: {hw_rmse}")
                        else:
                            print(f"⚠️ HW forecast boş")
                    else:
                        print(f"⚠️ HW için veri yetersiz ({len(historical)} hafta)")
                except Exception as e:
                    print(f"⚠️ HW hatası: {e}")

                # 2. ARIMA
                try:
                    if len(historical) >= 8:
                        print(f"🔄 ARIMA deneniyor...")
                        arima_result = forecaster.arima_forecast(historical, request.horizon)
                        arima_forecast = arima_result.get('mean', [])
                        if arima_forecast and len(arima_forecast) > 0:
                            arima_rmse = forecaster.calculate_model_rmse(historical, arima_forecast)
                            model_comparison['arima'] = {
                                'rmse': arima_rmse,
                                'forecast': arima_forecast
                            }
                            print(f"✅ ARIMA RMSE: {arima_rmse}")
                        else:
                            print(f"⚠️ ARIMA forecast boş")
                    else:
                        print(f"⚠️ ARIMA için veri yetersiz ({len(historical)} hafta)")
                except Exception as e:
                    print(f"⚠️ ARIMA hatası: {e}")

                # 3. Basit Model (her zaman çalışır)
                try:
                    print(f"🔄 Basit MA deneniyor...")
                    simple_result = forecaster.simple_forecast(historical, request.horizon)
                    simple_forecast = simple_result.get('mean', [])
                    if simple_forecast and len(simple_forecast) > 0:
                        simple_rmse = forecaster.calculate_model_rmse(historical, simple_forecast)
                        model_comparison['simple'] = {
                            'rmse': simple_rmse,
                            'forecast': simple_forecast
                        }
                        print(f"✅ Basit RMSE: {simple_rmse}")
                except Exception as e:
                    print(f"⚠️ Basit hatası: {e}")

                print(f"📊 Toplam model: {len(model_comparison)} - {list(model_comparison.keys())}")                

                # Outlier tespiti
                outlier_info = forecaster.detect_outliers(historical)
                
                # Trend analizi
                if len(historical) > 1:
                    trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                    trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                else:
                    trend_percent = 0
                    trend_direction = 'Sabit'
                
                # Model parametreleri
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
                
                # Cross-Validation bilgilerini ekle
                if 'selection_info' in forecast_result:
                    model_params.update(forecast_result['selection_info'])
                
                # Seçim nedeni
                selection_reason = forecast_result.get('selection_info', {}).get('selection_reason', 'Otomatik seçim')
                
                # Sonuçları topla
                result_item = {
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
                }
                results.append(result_item)
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir malzeme için tahmin yapılamadı!")
        
        # 3. Sonuçları kaydet (15 gün)
        # batch_forecast içinde
        from app.models import UserAnalysisResult

        # ✅ Her malzeme için ayrı kayıt oluştur
        for result in results:
            analysis_result = UserAnalysisResult(
                user_id=current_user.id,
                result_type='forecast_batch',  # ✅ result_type doğru
                material_code=result['material_code'],
                material_group=result.get('group', 'GENEL'),
                result_data={
                    'total': len(results),
                    'results': results,  # Tüm sonuçları içerir
                    'horizon': request.horizon,
                    'model_type': request.model_type
                },
                params={
                    'horizon': request.horizon,
                    'model_type': request.model_type,
                    'total_materials': len(results)
                },
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 8
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
    """
    Async olarak batch forecast başlatır. Hemen bir task_id döner.
    Token maliyeti: 8 token (middleware tarafından otomatik düşülür)
    """
    # 1. Cache'ten verileri al
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
    
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    # 2. Benzersiz bir task ID oluştur
    task_id = str(uuid.uuid4())
    
    # ✅ 3. İşlem başladığında AnalysisResult'a kayıt ekle
    from app.models import AnalysisResult
    
    initial_data = {
        'status': 'processing',
        'message': 'Analiz başlatıldı, işleniyor...',
        'total': len(materials),
        'results': [],
        'horizon': request.horizon,
        'model_type': request.model_type,
        'task_id': task_id,
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
    
    # 4. Arka plan görevini başlat
    background_tasks.add_task(
        run_async_forecast_job,
        task_id=task_id,
        user_id=current_user.id,
        request=request,
        db=db  # ✅ Session geç
    )
    
    return {
        "task_id": task_id, 
        "status": "started", 
        "message": "Analiz arka planda başlatıldı.",
        "token_cost": 8
    }

def run_async_forecast_job(task_id: str, user_id: int, request: ForecastRequest, db: Session):
    """Async batch forecast işini gerçekleştirir."""
    try:
        print(f"🔄 Async job başladı: Task ID {task_id}, Kullanıcı {user_id}")
        
        # Cache'ten verileri al
        cached_data = get_user_upload_data(user_id)
        if not cached_data:
            print(f"❌ Async job hatası: Veri bulunamadı (Task {task_id})")
            # ✅ Hata durumunda güncelle
            update_async_task_status(db, task_id, 'failed', 'Veri bulunamadı')
            return
        
        materials = cached_data.get('materials', [])
        if not materials:
            print(f"❌ Async job hatası: Malzeme bulunamadı (Task {task_id})")
            update_async_task_status(db, task_id, 'failed', 'Malzeme bulunamadı')
            return
        
        forecaster = DemandForecaster(seasonal_periods=52)
        results = []
        
        for idx, material in enumerate(materials):
            try:
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                # Ana tahmin
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                # Model karşılaştırması
                model_comparison = {}
                
                # 1. Holt-Winters
                try:
                    if len(historical) >= 6:
                        hw_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        hw_forecast = hw_result.get('mean', [])
                        if hw_forecast:
                            hw_rmse = forecaster.calculate_model_rmse(historical, hw_forecast)
                            model_comparison['holt_winters'] = {
                                'rmse': hw_rmse,
                                'forecast': hw_forecast
                            }
                except Exception as e:
                    print(f"⚠️ HW hatası: {e}")
                
                # 2. ARIMA
                try:
                    if len(historical) >= 6:
                        arima_result = forecaster.arima_forecast(historical, request.horizon)
                        arima_forecast = arima_result.get('mean', [])
                        if arima_forecast:
                            arima_rmse = forecaster.calculate_model_rmse(historical, arima_forecast)
                            model_comparison['arima'] = {
                                'rmse': arima_rmse,
                                'forecast': arima_forecast
                            }
                except Exception as e:
                    print(f"⚠️ ARIMA hatası: {e}")
                
                # 3. Basit Model
                simple_result = forecaster.simple_forecast(historical, request.horizon)
                simple_forecast = simple_result.get('mean', [])
                if simple_forecast:
                    simple_rmse = forecaster.calculate_model_rmse(historical, simple_forecast)
                    model_comparison['simple'] = {
                        'rmse': simple_rmse,
                        'forecast': simple_forecast
                    }
                
                # Outlier tespiti
                outlier_info = forecaster.detect_outliers(historical)
                
                # Trend analizi
                if len(historical) > 1:
                    trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                    trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                else:
                    trend_percent = 0
                    trend_direction = 'Sabit'
                
                # Model parametreleri
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
                
                # ✅ İlerleme güncelle
                progress = int((idx + 1) / len(materials) * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Malzeme {material.get('code', '')} tahmin hatası (Task {task_id}): {e}")
                continue
        
        if not results:
            print(f"❌ Async job hatası: Hiçbir sonuç yok (Task {task_id})")
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
        # ✅ Sonuçları kaydet - Güncelle
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'horizon': request.horizon,
            'model_type': request.model_type,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Analiz tamamlandı!',
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # ✅ Varolan kaydı güncelle
        db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).update({
            'data': result_data
        })
        db.commit()
        
        print(f"✅ Async job tamamlandı: Task ID {task_id}, {len(results)} malzeme analiz edildi")
        
    except Exception as e:
        print(f"❌ Async job hatası (Task {task_id}): {e}")
        update_async_task_status(db, task_id, 'failed', str(e))


# ✅ Yardımcı fonksiyonlar
def update_async_progress(db: Session, task_id: str, progress: int, message: str, completed: int):
    """Async işlem ilerlemesini güncelle"""
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['progress'] = progress
        data['message'] = message
        data['completed_materials'] = completed
        result.data = data
        db.commit()


def update_async_task_status(db: Session, task_id: str, status: str, message: str):
    """Async işlem durumunu güncelle"""
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['status'] = status
        data['message'] = message
        result.data = data
        db.commit()
 
@router.get("/forecast/async/status/{task_id}")
def get_async_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Async işlemin durumunu kontrol eder."""
    from app.models import AnalysisResult
    
    try:
        # ✅ Sorguyu optimize et
        result = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if result:
            return {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "message": "Analiz tamamlandı!"
            }
        
        # ✅ İşlem devam ediyor - progress'i tahmini göster
        # Gerçek ilerleme için cache veya Redis kullanılabilir
        return {
            "task_id": task_id,
            "status": "processing",
            "progress": 50,
            "message": "Analiz devam ediyor..."
        }
    except Exception as e:
        print(f"❌ Status kontrol hatası: {e}")
        # ✅ Hata durumunda da düzgün yanıt dön
        return {
            "task_id": task_id,
            "status": "error",
            "progress": 0,
            "message": f"Hata: {str(e)}"
        }


@router.get("/forecast/async/result/{task_id}")
def get_async_task_result(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Async işlemin sonuçlarını getirir."""
    from app.models import AnalysisResult
    
    try:
        result = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if not result:
            # ✅ 404 yerine 202 (Accepted) dönebilir
            raise HTTPException(status_code=404, detail="Task bulunamadı veya henüz tamamlanmadı")
        
        data = result.data
        return {
            'success': True,
            'total': data.get('total', 0),
            'results': data.get('results', [])
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Result getirme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
