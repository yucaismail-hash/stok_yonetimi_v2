"""
Talep Tahmini (Forecast) Modülü
Desteklenen modeller: Holt-Winters, ARIMA, Basit Hareketli Ortalama
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Uyarı: statsmodels kurulu değil. Sadece basit modeller kullanılabilir.")

class DemandForecaster:
    """Talep Tahmin Sınıfı - Holt-Winters, ARIMA, Basit"""
    
    def __init__(self, seasonal_periods=52):
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.model_type = None
        self.fitted = False
    
    def auto_select_model(self, historical_data) -> Tuple[str, Dict]:
        """Otomatik model seçimi - basit ve güvenilir"""
        n = len(historical_data)
        
        # Veri yetersizse basit dön
        if n < 8:
            return "simple", {"selection_reason": "Yetersiz veri, basit model kullanıldı"}
        
        # Mevsimsellik kontrolü
        seasonal_periods = min(52, max(4, n // 4))
        
        # Modelleri test et
        models = []
        if STATSMODELS_AVAILABLE and n >= seasonal_periods * 2:
            models.append('holt_winters')
        if STATSMODELS_AVAILABLE and n >= 12:
            models.append('arima')
        models.append('simple')
        
        # Walk-Forward Validation
        test_size = min(4, n // 4)
        if test_size < 2:
            test_size = 2
        
        best_mape = float('inf')
        best_model = 'simple'
        scores = {}
        
        for model_name in models:
            mape_list = []
            
            for i in range(test_size, n - test_size + 1):
                train = historical_data[:i]
                test = historical_data[i:i+test_size]
                
                try:
                    # Model tahmini
                    if model_name == 'holt_winters':
                        result = self.holt_winters_forecast(train, horizon=test_size)
                    elif model_name == 'arima':
                        result = self.arima_forecast(train, horizon=test_size)
                    else:
                        result = self.simple_forecast(train, horizon=test_size)
                    
                    pred = result.get('mean', [])
                    if not pred:
                        continue
                    
                    # MAPE hesapla
                    for actual, pred_val in zip(test, pred):
                        if actual > 0:
                            mape_list.append(abs((actual - pred_val) / actual) * 100)
                        else:
                            mape_list.append(0 if pred_val == 0 else 100)
                            
                except Exception as e:
                    continue
            
            if mape_list:
                avg_mape = np.mean(mape_list)
                scores[model_name] = avg_mape
                if avg_mape < best_mape:
                    best_mape = avg_mape
                    best_model = model_name
        
        # Sonuçları döndür
        selection_info = {
            "selection_method": "Walk-Forward CV",
            "models_tested": len(scores),
            "best_model": best_model,
            "best_mape": round(best_mape, 2) if best_mape != float('inf') else 999,
            "model_scores": {k: round(v, 2) for k, v in scores.items()},
            "selection_reason": f"En düşük MAPE ile '{best_model}' seçildi"
        }
        
        return best_model, selection_info

    def holt_winters_forecast(self, data, horizon=13, seasonal_periods=None):
        """Holt-Winters Mevsimsel Model ile Tahmin"""
        n = len(data)
        
        # ✅ Mevsimsellik periyodunu veriye göre ayarla
        if seasonal_periods is None:
            seasonal_periods = min(self.seasonal_periods, max(4, n // 4))
        
        # ✅ Veri en az 8 hafta ve seasonal_periods * 2 olmalı
        if n < 8 or n < seasonal_periods * 2:
            print(f"⚠️ HW için veri yetersiz ({n} hafta, {seasonal_periods} periyot) - Basit modele dönülüyor")
            return self.simple_forecast(data, horizon)
        
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
            # ✅ Trend kontrolü
            has_trend = n > 12 and abs(np.polyfit(range(n), data, 1)[0]) > 0.01
            
            if has_trend and n >= seasonal_periods * 2:
                model = ExponentialSmoothing(
                    data,
                    seasonal_periods=seasonal_periods,
                    trend='add',
                    seasonal='add',
                    initialization_method='estimated'
                )
            else:
                model = ExponentialSmoothing(
                    data,
                    seasonal_periods=seasonal_periods,
                    trend=None,
                    seasonal='add',
                    initialization_method='estimated'
                )
            
            fitted = model.fit()
            forecast = fitted.forecast(horizon)
            
            if hasattr(forecast, 'values'):
                forecast_mean = forecast.values
            else:
                forecast_mean = np.array(forecast)
            
            residual_std = np.std(fitted.resid) if len(fitted.resid) > 0 else np.std(data) * 0.1
            
            lower_80 = forecast_mean - stats.norm.ppf(0.9) * residual_std
            upper_80 = forecast_mean + stats.norm.ppf(0.9) * residual_std
            lower_95 = forecast_mean - stats.norm.ppf(0.975) * residual_std
            upper_95 = forecast_mean + stats.norm.ppf(0.975) * residual_std
            
            return {
                'mean': forecast_mean.tolist(),
                'lower_80': lower_80.tolist(),
                'upper_80': upper_80.tolist(),
                'lower_95': lower_95.tolist(),
                'upper_95': upper_95.tolist(),
                'model_used': 'holt_winters'
            }
        except Exception as e:
            print(f"⚠️ Holt-Winters hatası: {e}")
            return self.simple_forecast(data, horizon)


    def arima_forecast(self, data, horizon=13, order=(1,1,1)):
        """ARIMA Modeli ile Tahmin"""
        n = len(data)
        
        # ✅ ARIMA için en az 8 hafta gerekli
        if n < 8:
            print(f"⚠️ ARIMA için veri yetersiz ({n} hafta) - Basit modele dönülüyor")
            return self.simple_forecast(data, horizon)
        
        try:
            # ✅ Otomatik order seçimi
            best_aic = float('inf')
            best_order = order
            
            # Grid search (sadece veri yeterliyse)
            if n >= 12:
                for p in range(0, min(3, n//4)):
                    for d in range(0, 2):
                        for q in range(0, min(3, n//4)):
                            if p == 0 and d == 0 and q == 0:
                                continue
                            try:
                                model = ARIMA(data, order=(p, d, q))
                                fitted = model.fit()
                                if fitted.aic < best_aic:
                                    best_aic = fitted.aic
                                    best_order = (p, d, q)
                            except:
                                continue
                print(f"📊 ARIMA en iyi order: {best_order}, AIC: {best_aic:.2f}")
            
            model = ARIMA(data, order=best_order)
            fitted = model.fit()
            forecast_result = fitted.forecast(horizon)
            
            if hasattr(forecast_result, 'values'):
                forecast_mean = forecast_result.values
            else:
                forecast_mean = np.array(forecast_result)
            
            residual_std = np.std(fitted.resid) if len(fitted.resid) > 0 else np.std(data) * 0.1
            
            lower_80 = forecast_mean - stats.norm.ppf(0.9) * residual_std
            upper_80 = forecast_mean + stats.norm.ppf(0.9) * residual_std
            lower_95 = forecast_mean - stats.norm.ppf(0.975) * residual_std
            upper_95 = forecast_mean + stats.norm.ppf(0.975) * residual_std
            
            return {
                'mean': forecast_mean.tolist(),
                'lower_80': lower_80.tolist(),
                'upper_80': upper_80.tolist(),
                'lower_95': lower_95.tolist(),
                'upper_95': upper_95.tolist(),
                'model_used': 'arima'
            }
        except Exception as e:
            print(f"⚠️ ARIMA hatası: {e}")
            return self.simple_forecast(data, horizon)

    def simple_forecast(self, data, horizon=13):
        """Basit Hareketli Ortalama + Eğilim ile Tahmin"""
        n = len(data)
        if n < 4:
            last_value = data[-1] if data else 0
            forecast_mean = [last_value] * horizon
            residual_std = np.std(data) if len(data) > 1 else max(last_value * 0.1, 1)
        else:
            weights = [0.4, 0.3, 0.2, 0.1]
            weighted_avg = sum(data[-4:][i] * weights[i] for i in range(4))
            
            if n >= 8:
                x = np.arange(8)
                y = data[-8:]
                slope = np.polyfit(x, y, 1)[0]
            else:
                x = np.arange(n)
                y = data
                slope = np.polyfit(x, y, 1)[0] if n > 1 else 0
            
            forecast_mean = []
            for i in range(horizon):
                pred = weighted_avg + slope * (i + 1)
                forecast_mean.append(max(0, pred))
            residual_std = np.std(data[-8:]) if n >= 8 else weighted_avg * 0.2
        
        forecast_mean = np.array(forecast_mean)
        forecast_mean = np.maximum(forecast_mean, 0)
        
        lower_80 = forecast_mean - stats.norm.ppf(0.9) * residual_std
        upper_80 = forecast_mean + stats.norm.ppf(0.9) * residual_std
        lower_95 = forecast_mean - stats.norm.ppf(0.975) * residual_std
        upper_95 = forecast_mean + stats.norm.ppf(0.975) * residual_std
        
        return {
            'mean': forecast_mean.tolist(),
            'lower_80': np.maximum(lower_80, 0).tolist(),
            'upper_80': upper_80.tolist(),
            'lower_95': np.maximum(lower_95, 0).tolist(),
            'upper_95': upper_95.tolist(),
            'model_used': 'simple'
        }
    
    def forecast(self, historical_data, horizon=13, model_type="auto"):
        """Ana forecast fonksiyonu"""
        if not historical_data or len(historical_data) < 4:
            raise ValueError("Yetersiz veri: En az 4 haftalık veri gerekli")
        
        selection_info = {}
        
        if model_type == "auto":
            model_type, selection_info = self.auto_select_model(historical_data)
        
        # Seçilen model ile tahmin yap
        if model_type == "holt_winters" and STATSMODELS_AVAILABLE:
            result = self.holt_winters_forecast(historical_data, horizon)
        elif model_type == "arima" and STATSMODELS_AVAILABLE:
            result = self.arima_forecast(historical_data, horizon)
        else:
            result = self.simple_forecast(historical_data, horizon)
            result['model_used'] = 'simple'
        
        result['selection_info'] = selection_info
        return result
    
    def get_forecast_accuracy(self, historical_data, test_horizon=4):
        """Forecast doğruluğunu test et"""
        if len(historical_data) < test_horizon + 4:
            return {'mape': 999, 'accuracy_level': 'YETERSİZ_VERİ'}
        
        train = historical_data[:-test_horizon]
        test = historical_data[-test_horizon:]
        
        if len(train) < 4:
            return {'mape': 999, 'accuracy_level': 'YETERSİZ_VERİ'}
        
        try:
            forecast_result = self.forecast(train, horizon=test_horizon, model_type="auto")
            forecast_mean = forecast_result.get('mean', [])
            if not forecast_mean:
                forecast_mean = [np.mean(train)] * test_horizon
        except:
            forecast_mean = [np.mean(train)] * test_horizon
        
        mape_values = []
        for actual, pred in zip(test, forecast_mean):
            if actual > 0:
                mape_values.append(abs((actual - pred) / actual) * 100)
            else:
                mape_values.append(0 if pred == 0 else 100)
        
        if mape_values:
            mape = np.mean(mape_values)
            return {
                'mape': round(mape, 2),
                'accuracy_level': 'YÜKSEK' if mape < 20 else ('ORTA' if mape < 40 else 'DÜŞÜK')
            }
        return {'mape': 999, 'accuracy_level': 'HESAPLANAMADI'}
    
    def calculate_model_rmse(self, historical_data: List[float], forecast: List[float], test_horizon: int = 4) -> float:
        """Belirli bir modelin RMSE'sini hesapla (MAPE olarak)"""
        if len(historical_data) < test_horizon + 4:
            return 999
        
        test = historical_data[-test_horizon:]
        
        if len(forecast) < test_horizon:
            pred = forecast + [forecast[-1]] * (test_horizon - len(forecast)) if forecast else [0] * test_horizon
        else:
            pred = forecast[:test_horizon]
        
        mape_values = []
        for actual, pred_val in zip(test, pred):
            if actual > 0:
                mape_values.append(abs((actual - pred_val) / actual) * 100)
            else:
                # Gerçek değer 0 ise, tahmin de 0'a yakınsa düşük hata ver
                if pred_val == 0:
                    mape_values.append(0)
                else:
                    mape_values.append(100)
        
        if mape_values:
            return round(np.mean(mape_values), 2)
        return 999

    def detect_outliers(self, data: List[float], threshold: float = 2.5) -> Dict[str, Any]:
        """Verideki aykırı değerleri tespit et"""
        if not data:
            return {'has_outliers': False, 'outliers': [], 'total': 0, 'outlier_count': 0}
        
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        outliers = []
        for i, val in enumerate(data):
            if std_val > 0 and abs(val - mean_val) / std_val > threshold:
                outliers.append({'index': i + 1, 'value': val, 'week': i + 1})
        
        return {
            'has_outliers': len(outliers) > 0,
            'outliers': outliers,
            'total': len(data),
            'outlier_count': len(outliers)
        }