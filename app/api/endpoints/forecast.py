from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.forecast import DemandForecaster
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import numpy as np
import itertools

router = APIRouter()
forecaster = DemandForecaster()

class ForecastRequest(BaseModel):
    historical_data: List[float]
    horizon: int = 4
    model_type: Optional[str] = "auto"

class BatchForecastRequest(BaseModel):
    horizon: int = 4  # ✅ Kullanıcı tarafından belirlenecek (4-52)
    model_type: str = "auto"


@router.post("/forecast")
def get_forecast(request: ForecastRequest):
    try:
        result = forecaster.forecast(
            request.historical_data,
            horizon=request.horizon,
            model_type=request.model_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/forecast/batch")
def forecast_batch(
    request: BatchForecastRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Forecast analizi - Kullanıcı model ve horizon seçebilir.
    Token maliyeti: 8 token
    """
    try:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        print(f"✅ {len(materials)} malzeme bulundu")
        
        horizon = request.horizon or 4  # ✅ Kullanıcı seçimi (4-52)
        user_model = request.model_type or "auto"
        
        print(f"📌 Kullanıcı seçimi: Model={user_model}, Horizon={horizon} hafta")
        
        # 📌 Model etiketleri
        model_labels = {
            'holt_winters': 'Holt-Winters (Mevsimsel)',
            'arima': 'ARIMA (Otoregresif)',
            'simple': 'Basit (MA+Trend)',
            'auto': 'Otomatik Seçim'
        }
        
        model_descriptions = {
            'holt_winters': 'Mevsimsel talep desenleri için uygundur. 52+ hafta veri önerilir.',
            'arima': 'Doğrusal trend ve otokorelasyon için uygundur. 26+ hafta veri önerilir.',
            'simple': 'Basit ve hızlı, son 4 haftanın ağırlıklı ortalamasını alır.',
            'auto': 'Veri uzunluğuna göre en uygun modeli otomatik seçer.'
        }
        
        results = []
        
        for material in materials:
            weekly_data = material.get('historical_demand', [])
            if len(weekly_data) < 4:
                print(f"⚠️ {material.get('code', 'Bilinmeyen')}: {len(weekly_data)} hafta veri (4+ gerekli)")
                continue
            
            print(f"✅ {material.get('code', 'Bilinmeyen')}: {len(weekly_data)} hafta veri ile forecast başlıyor...")
            
            try:
                # 📌 Kullanıcının seçtiği modeli kullan
                if user_model != "auto":
                    selected_model = user_model
                    result = forecaster.forecast(weekly_data, horizon=horizon, model_type=selected_model)
                    
                    # 📌 Seçilen modelin RMSE'sini hesapla
                    rmse = forecaster.get_forecast_accuracy(weekly_data, test_horizon=min(4, len(weekly_data)//2))
                    rmse_val = rmse.get('mape', 999) if rmse else 999
                    
                    # 📌 Diğer modelleri de hesapla (karşılaştırma için)
                    all_models = {}
                    for model_name in ['holt_winters', 'arima', 'simple', 'auto']:
                        try:
                            model_result = forecaster.forecast(weekly_data, horizon=horizon, model_type=model_name)
                            model_rmse = forecaster.get_forecast_accuracy(weekly_data, test_horizon=min(4, len(weekly_data)//2))
                            model_rmse_val = model_rmse.get('mape', 999) if model_rmse else 999
                            all_models[model_name] = {
                                'rmse': model_rmse_val,
                                'forecast': model_result.get('mean', [0] * horizon)[:horizon]
                            }
                        except:
                            all_models[model_name] = {'rmse': 999, 'forecast': [0] * horizon}
                    
                    selection_reason = f"Kullanıcı tarafından {model_labels.get(selected_model, selected_model)} seçildi."
                    
                    print(f"📌 Kullanıcı seçimi: {selected_model}, RMSE: {rmse_val}")
                    
                else:
                    # 📌 OTOMATİK SEÇİM - Tüm modelleri test et
                    all_models = {}
                    best_model = None
                    best_score = float('inf')
                    best_result = None
                    
                    for model_name in ['holt_winters', 'arima', 'simple', 'auto']:
                        try:
                            result = forecaster.forecast(weekly_data, horizon=horizon, model_type=model_name)
                            rmse = forecaster.get_forecast_accuracy(weekly_data, test_horizon=min(4, len(weekly_data)//2))
                            rmse_val = rmse.get('mape', 999) if rmse else 999
                            
                            all_models[model_name] = {
                                'rmse': rmse_val,
                                'forecast': result.get('mean', [0] * horizon)[:horizon]
                            }
                            
                            if rmse_val < best_score:
                                best_score = rmse_val
                                best_model = model_name
                                best_result = result
                        except Exception as e:
                            all_models[model_name] = {'rmse': 999, 'forecast': [0] * horizon}
                    
                    # 📌 En iyi modeli seç
                    if best_model is None:
                        best_model = 'simple'
                        best_result = forecaster.forecast(weekly_data, horizon=horizon, model_type='simple')
                        best_score = 999
                    
                    selected_model = best_model
                    result = best_result
                    
                    if best_score < 999:
                        selection_reason = f"En düşük MAPE ({best_score:.1f}%) ile {model_labels.get(best_model, best_model)} seçildi."
                    else:
                        selection_reason = "Veri yetersiz olduğu için basit model seçildi."
                    
                    print(f"📌 Otomatik seçim: {selected_model}, RMSE: {best_score}")
                
                # 📌 Tahmin değerleri
                forecast_mean = result.get('mean', [0] * horizon)[:horizon]
                lower_80 = result.get('lower_80', [0] * horizon)[:horizon]
                upper_80 = result.get('upper_80', [0] * horizon)[:horizon]
                lower_95 = result.get('lower_95', [0] * horizon)[:horizon]
                upper_95 = result.get('upper_95', [0] * horizon)[:horizon]
                
                # 📌 Trend
                if len(forecast_mean) >= 2:
                    trend_direction = "Artış" if forecast_mean[-1] > forecast_mean[0] else "Azalış" if forecast_mean[-1] < forecast_mean[0] else "Stabil"
                    trend_percent = ((forecast_mean[-1] - forecast_mean[0]) / forecast_mean[0] * 100) if forecast_mean[0] > 0 else 0
                else:
                    trend_direction = "Bilinmiyor"
                    trend_percent = 0
                
                # 📌 RMSE değeri
                rmse_val = all_models.get(selected_model, {}).get('rmse', 999)
                
                # 📌 Model karşılaştırma tablosu için
                model_comparison = {}
                for model_name, model_data in all_models.items():
                    model_comparison[model_name] = {
                        'rmse': model_data.get('rmse', 999),
                        'forecast': model_data.get('forecast', [0] * horizon)[:horizon]
                    }
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': horizon,
                    'selected_model': selected_model,
                    'best_model_label': model_labels.get(selected_model, selected_model),
                    'model_description': model_descriptions.get(selected_model, ''),
                    'selection_reason': selection_reason,
                    'forecast': [round(f, 1) for f in forecast_mean],
                    'lower_80': [round(f, 1) for f in lower_80],
                    'upper_80': [round(f, 1) for f in upper_80],
                    'lower_95': [round(f, 1) for f in lower_95],
                    'upper_95': [round(f, 1) for f in upper_95],
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': rmse_val if rmse_val < 999 else None,
                    'model_comparison': model_comparison
                })
                
                print(f"✅ {material.get('code')}: Seçilen = {selected_model}, RMSE = {rmse_val}")
                
            except Exception as e:
                print(f"❌ Forecast hatası ({material.get('code', 'Bilinmeyen')}): {e}")
                continue
        
        if results:
            from app.models import UserAnalysisResult
            
            for result in results:
                analysis_result = UserAnalysisResult(
                    user_id=current_user.id,
                    result_type='forecast_batch',
                    material_code=result['material_code'],
                    material_group=result.get('group', 'GENEL'),
                    result_data=result,
                    params={'horizon': horizon, 'model_type': user_model, 'total_materials': len(results)},
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
        print(f"❌ Forecast batch hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))