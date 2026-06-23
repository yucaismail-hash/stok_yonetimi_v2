"""
Talep Tahmini (Forecast) Modülü
Desteklenen modeller: Holt-Winters, ARIMA, Basit Hareketli Ortalama
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller, acf, pacf
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
        
    def auto_select_model(self, historical_data, max_arima_order=(3,1,2)):
        """Otomatik model seçimi (AIC/BIC bazlı)"""
        if not STATSMODELS_AVAILABLE:
            return "simple"
        
        data = pd.Series(historical_data)
        n = len(data)
        
        if n >= 52:
            return "holt_winters"
        elif n >= 26:
            try:
                best_aic = float('inf')
                for p in range(0, min(3, n//6)):
                    for d in range(0, 2):
                        for q in range(0, 2):
                            try:
                                model = ARIMA(data, order=(p,d,q))
                                fitted = model.fit()
                                if fitted.aic < best_aic:
                                    best_aic = fitted.aic
                            except:
                                pass
                return "arima" if best_aic != float('inf') else "simple"
            except:
                return "simple"
        else:
            return "simple"
    
    def holt_winters_forecast(self, data, horizon=13, seasonal_periods=None):
        """Holt-Winters Mevsimsel Model ile Tahmin"""
        if seasonal_periods is None:
            seasonal_periods = min(self.seasonal_periods, len(data) // 2)
        
        if len(data) < seasonal_periods * 2:
            from statsmodels.tsa.holtwinters import SimpleExpSmoothing
            model = SimpleExpSmoothing(data)
            fitted = model.fit()
            forecast = fitted.forecast(horizon)
            residual_std = np.std(fitted.resid) if len(fitted.resid) > 0 else np.std(data) * 0.1
        else:
            model = ExponentialSmoothing(
                data, 
                seasonal_periods=seasonal_periods,
                trend='add',
                seasonal='add'
            )
            fitted = model.fit()
            forecast = fitted.forecast(horizon)
            residual_std = np.std(fitted.resid) if len(fitted.resid) > 0 else np.std(data) * 0.1
        
        forecast_mean = forecast.values
        lower_80 = forecast_mean - stats.norm.ppf(0.9) * residual_std
        upper_80 = forecast_mean + stats.norm.ppf(0.9) * residual_std
        lower_95 = forecast_mean - stats.norm.ppf(0.975) * residual_std
        upper_95 = forecast_mean + stats.norm.ppf(0.975) * residual_std
        
        return {
            'mean': forecast_mean.tolist(),
            'lower_80': lower_80.tolist(),
            'upper_80': upper_80.tolist(),
            'lower_95': lower_95.tolist(),
            'upper_95': upper_95.tolist()
        }
    
    def arima_forecast(self, data, horizon=13, order=(1,1,1)):
        """ARIMA Modeli ile Tahmin"""
        model = ARIMA(data, order=order)
        fitted = model.fit()
        forecast_result = fitted.forecast(horizon)
        
        forecast_mean = forecast_result.values
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
            'upper_95': upper_95.tolist()
        }
    
    def simple_forecast(self, data, horizon=13):
        """Basit Hareketli Ortalama + Eğilim ile Tahmin"""
        n = len(data)
        if n < 4:
            last_value = data[-1] if data else 0
            forecast_mean = [last_value] * horizon
            residual_std = np.std(data) if len(data) > 1 else last_value * 0.1
        else:
            weights = [0.4, 0.3, 0.2, 0.1]
            weighted_avg = sum(data[-4:][i] * weights[i] for i in range(4))
            
            x = np.arange(4)
            y = data[-4:]
            slope = np.polyfit(x, y, 1)[0]
            
            forecast_mean = []
            for i in range(horizon):
                pred = weighted_avg + slope * (i + 1)
                forecast_mean.append(max(0, pred))
            residual_std = np.std(data[-8:]) if len(data) >= 8 else weighted_avg * 0.2
        
        forecast_mean = np.array(forecast_mean)
        lower_80 = forecast_mean - stats.norm.ppf(0.9) * residual_std
        upper_80 = forecast_mean + stats.norm.ppf(0.9) * residual_std
        lower_95 = forecast_mean - stats.norm.ppf(0.975) * residual_std
        upper_95 = forecast_mean + stats.norm.ppf(0.975) * residual_std
        
        return {
            'mean': forecast_mean.tolist(),
            'lower_80': np.maximum(lower_80, 0).tolist(),
            'upper_80': upper_80.tolist(),
            'lower_95': np.maximum(lower_95, 0).tolist(),
            'upper_95': upper_95.tolist()
        }
    
    def forecast(self, historical_data, horizon=13, model_type="auto"):
        """
        Ana forecast fonksiyonu
        
        Args:
            historical_data: List[float] - Haftalık talep verisi
            horizon: int - Tahmin edilecek hafta sayısı
            model_type: str - "auto", "holt_winters", "arima", "simple"
        
        Returns:
            dict: mean, lower_80, upper_80, lower_95, upper_95
        """
        if not historical_data or len(historical_data) < 4:
            raise ValueError("Yetersiz veri: En az 4 haftalık veri gerekli")
        
        data = pd.Series(historical_data)
        
        if model_type == "auto":
            model_type = self.auto_select_model(historical_data)
        
        if model_type == "holt_winters" and STATSMODELS_AVAILABLE:
            result = self.holt_winters_forecast(data, horizon)
            result['model_used'] = 'holt_winters'
        elif model_type == "arima" and STATSMODELS_AVAILABLE:
            result = self.arima_forecast(data, horizon)
            result['model_used'] = 'arima'
        else:
            result = self.simple_forecast(historical_data, horizon)
            result['model_used'] = 'simple'
        
        return result
    
    def get_forecast_accuracy(self, historical_data, test_horizon=4):
        """
        Forecast doğruluğunu test et (MAPE hesapla)
        """
        if len(historical_data) < test_horizon + 4:
            return {'mape': 999, 'accuracy_level': 'YETERSİZ_VERİ'}
        
        train = historical_data[:-test_horizon]
        test = historical_data[-test_horizon:]
        
        if len(train) < 4:
            return {'mape': 999, 'accuracy_level': 'YETERSİZ_VERİ'}
        
        try:
            forecast_result = self.forecast(train, horizon=test_horizon, model_type="auto")
            forecast_mean = forecast_result['mean']
        except:
            forecast_mean = [np.mean(train)] * test_horizon
        
        mape_values = []
        for actual, pred in zip(test, forecast_mean):
            if actual > 0:
                mape_values.append(abs((actual - pred) / actual) * 100)
            else:
                mape_values.append(100)
        
        if mape_values:
            mape = np.mean(mape_values)
            return {
                'mape': round(mape, 2),
                'accuracy_level': 'YÜKSEK' if mape < 20 else ('ORTA' if mape < 40 else 'DÜŞÜK')
            }
        return {'mape': 999, 'accuracy_level': 'HESAPLANAMADI'}
    
    def compare_models(self, historical_data: List[float], horizon: int = 4) -> Dict[str, Any]:
        """
        Tüm modelleri karşılaştır ve en iyisini seç
        """
        results = {}
        best_model = None
        best_rmse = float('inf')
        
        models_to_test = ['holt_winters', 'arima', 'simple']
        
        for model_name in models_to_test:
            try:
                result = self.forecast(historical_data, horizon=horizon, model_type=model_name)
                metrics = self._calculate_metrics(historical_data, result['mean'][:len(historical_data)])
                result['metrics'] = metrics
                results[model_name] = result
                
                if metrics['rmse'] < best_rmse:
                    best_rmse = metrics['rmse']
                    best_model = model_name
            except Exception as e:
                results[model_name] = {'error': str(e)}
        
        # Auto model
        try:
            auto_result = self.forecast(historical_data, horizon=horizon, model_type="auto")
            metrics = self._calculate_metrics(historical_data, auto_result['mean'][:len(historical_data)])
            auto_result['metrics'] = metrics
            results['auto'] = auto_result
            
            if metrics['rmse'] < best_rmse:
                best_rmse = metrics['rmse']
                best_model = 'auto'
        except Exception as e:
            results['auto'] = {'error': str(e)}
        
        if best_model is None:
            best_model = 'simple'
            best_rmse = results.get('simple', {}).get('metrics', {}).get('rmse', 0)
        
        return {
            'results': results,
            'best_model': best_model,
            'best_rmse': best_rmse if best_rmse != float('inf') else None
        }
    
    def _calculate_metrics(self, actual: List[float], predicted: List[float]) -> Dict[str, float]:
        """Hata metriklerini hesapla"""
        actual = actual[:len(predicted)]
        n = len(actual)
        if n == 0:
            return {'mae': 0, 'mse': 0, 'rmse': 0}
        
        mae = np.mean(np.abs(np.array(actual) - np.array(predicted)))
        mse = np.mean((np.array(actual) - np.array(predicted)) ** 2)
        rmse = np.sqrt(mse)
        
        return {'mae': float(mae), 'mse': float(mse), 'rmse': float(rmse)}