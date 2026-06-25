from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.forecast import DemandForecaster
from app.auth import get_current_user
from app.models import User, TokenCost
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import numpy as np

router = APIRouter()
forecaster = DemandForecaster()

class ForecastRequest(BaseModel):
    historical_data: List[float]
    horizon: int = 4
    model_type: Optional[str] = "auto"

class BatchForecastRequest(BaseModel):
    horizon: int = 4
    model_type: str = "auto"


@router.get("/cost")
def get_forecast_cost(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Forecast analizi token maliyetini getir
    """
    token_cost = db.query(TokenCost).filter(
        TokenCost.endpoint == "/api/forecast/batch",
        TokenCost.method == "POST",
        TokenCost.is_active == True
    ).first()
    
    cost = token_cost.cost if token_cost else 8
    
    return {
        'cost': cost,
        'endpoint': '/api/forecast/batch',
        'method': 'POST'
    }


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
    """Toplu Forecast analizi - Kullanıcı model ve horizon seçebilir. Token: 8"""
    try:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        print(f"✅ {len(materials)} malzeme bulundu")
        
        horizon = request.horizon or 4
        user_model = request.model_type or "auto"
        
        print(f"📌 Kullanıcı seçimi: Model={user_model}, Horizon={horizon} hafta")
        
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
                outlier_result = forecaster.detect_outliers(weekly_data)
                
                all_models = {}
                best_model = None
                best_score = float('inf')
                best_result = None
                
                for model_name in ['holt_winters', 'arima', 'simple', 'auto']:
                    try:
                        result = forecaster.forecast(weekly_data, horizon=horizon, model_type=model_name)
                        forecast_mean = result.get('mean', [0] * horizon)
                        model_rmse = forecaster.calculate_model_rmse(weekly_data, forecast_mean, test_horizon=min(4, len(weekly_data)//2))
                        
                        all_models[model_name] = {
                            'rmse': model_rmse,
                            'forecast': forecast_mean[:horizon]
                        }
                        
                        if user_model != "auto":
                            if model_name == user_model:
                                best_model = model_name
                                best_result = result
                                best_score = model_rmse
                        else:
                            if model_rmse < best_score:
                                best_score = model_rmse
                                best_model = model_name
                                best_result = result
                                
                    except Exception as e:
                        all_models[model_name] = {'rmse': 999, 'forecast': [0] * horizon}
                        print(f"⚠️ {model_name} hatası: {e}")
                
                if user_model != "auto" and best_model is None:
                    best_score = 999
                    for model_name in ['holt_winters', 'arima', 'simple', 'auto']:
                        if all_models[model_name]['rmse'] < best_score:
                            best_score = all_models[model_name]['rmse']
                            best_model = model_name
                            try:
                                best_result = forecaster.forecast(weekly_data, horizon=horizon, model_type=best_model)
                            except:
                                best_result = {'mean': all_models[best_model]['forecast']}
                
                if best_model is None:
                    best_model = 'simple'
                    try:
                        best_result = forecaster.forecast(weekly_data, horizon=horizon, model_type='simple')
                    except:
                        best_result = {'mean': [0] * horizon, 'lower_80': [0] * horizon, 'upper_80': [0] * horizon, 'lower_95': [0] * horizon, 'upper_95': [0] * horizon}
                    best_score = all_models.get('simple', {}).get('rmse', 999)
                
                forecast_mean = best_result.get('mean', [0] * horizon)[:horizon]
                lower_80 = best_result.get('lower_80', [0] * horizon)[:horizon]
                upper_80 = best_result.get('upper_80', [0] * horizon)[:horizon]
                lower_95 = best_result.get('lower_95', [0] * horizon)[:horizon]
                upper_95 = best_result.get('upper_95', [0] * horizon)[:horizon]
                
                if len(forecast_mean) >= 2:
                    trend_direction = "Artış" if forecast_mean[-1] > forecast_mean[0] else "Azalış" if forecast_mean[-1] < forecast_mean[0] else "Stabil"
                    trend_percent = ((forecast_mean[-1] - forecast_mean[0]) / forecast_mean[0] * 100) if forecast_mean[0] > 0 else 0
                else:
                    trend_direction = "Bilinmiyor"
                    trend_percent = 0
                
                if user_model != "auto":
                    selection_reason = f"Kullanıcı tarafından {model_labels.get(best_model, best_model)} seçildi."
                else:
                    if best_score < 999:
                        selection_reason = f"En düşük MAPE ({best_score:.1f}%) ile {model_labels.get(best_model, best_model)} seçildi."
                    else:
                        selection_reason = "Veri yetersiz olduğu için basit model seçildi."
                
                model_params = {}
                if best_model == 'holt_winters':
                    model_params = {
                        'seasonal_periods': min(52, len(weekly_data) // 2),
                        'trend': 'add',
                        'seasonal': 'add'
                    }
                elif best_model == 'arima':
                    model_params = {
                        'p': 1,
                        'd': 1,
                        'q': 1,
                        'order': '(1,1,1)'
                    }
                elif best_model == 'simple':
                    model_params = {
                        'window': 4,
                        'weights': '[0.4, 0.3, 0.2, 0.1]'
                    }
                else:  # auto
                    model_params = {
                        'selection_method': 'MAPE based',
                        'models_tested': len(all_models)
                    }
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': horizon,
                    'selected_model': best_model,
                    'best_model_label': model_labels.get(best_model, best_model),
                    'model_description': model_descriptions.get(best_model, ''),
                    'selection_reason': selection_reason,
                    'forecast': [round(f, 1) for f in forecast_mean],
                    'lower_80': [round(f, 1) for f in lower_80],
                    'upper_80': [round(f, 1) for f in upper_80],
                    'lower_95': [round(f, 1) for f in lower_95],
                    'upper_95': [round(f, 1) for f in upper_95],
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': best_score if best_score < 999 else None,
                    'model_comparison': all_models,
                    'model_params': model_params,
                    'outlier_info': outlier_result,
                    'historical_data': weekly_data
                })
                
                print(f"✅ {material.get('code')}: Seçilen = {best_model}, RMSE = {best_score}")
                
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


@router.get("/info")
def get_forecast_info():
    return {
        "available_models": [
            {"key": "auto", "label": "Otomatik Seçim", "description": "Veriye göre en iyi modeli seçer"},
            {"key": "holt_winters", "label": "Holt-Winters (Mevsimsel)", "description": "52+ hafta veri önerilir"},
            {"key": "arima", "label": "ARIMA (Otoregresif)", "description": "26+ hafta veri önerilir"},
            {"key": "simple", "label": "Basit (MA+Trend)", "description": "Hızlı, az veri için ideal"}
        ]
    }