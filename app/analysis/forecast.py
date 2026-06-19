"""
Talep Tahmini (Forecast) Modülü
Desteklenen modeller: Holt-Winters, ARIMA, Basit Hareketli Ortalama
"""

import numpy as np
import pandas as pd
from scipy import stats
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
        self.seasonal_periods = seasonal_periods  # Haftalık veri için yıllık mevsimsellik
        self.model = None
        self.model_type = None
        self.fitted = False
        
    def auto_select_model(self, historical_data, max_arima_order=(3,1,2)):
        """Otomatik model seçimi (AIC/BIC bazlı)"""
        if not STATSMODELS_AVAILABLE:
            return "simple"
        
        data = pd.Series(historical_data)
        n = len(data)
        
        # Veri uzunluğuna göre model seçimi
        if n >= 52:  # 1 yıl veya daha fazla veri varsa
            return "holt_winters"
        elif n >= 26:  # 6 ay veri varsa
            # ARIMA dene, başarısız olursa simple
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
        
        # Mevsimsellik kontrolü
        if len(data) < seasonal_periods * 2:
            # Yetersiz veri: basit exponential smoothing (mevsimsiz)
            from statsmodels.tsa.holtwinters import SimpleExpSmoothing
            model = SimpleExpSmoothing(data)
            fitted = model.fit()
            forecast = fitted.forecast(horizon)
            residual_std = np.std(fitted.resid) if len(fitted.resid) > 0 else np.std(data) * 0.1
        else:
            # Tam mevsimsel model
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
        
        # Güven aralıkları
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
        """Basit Hareketli Ortalama + Eğilim ile Tahmin (statsmodels yoksa fallback)"""
        n = len(data)
        if n < 4:
            # Veri çok az: son değeri tekrarla
            last_value = data[-1] if data else 0
            forecast_mean = [last_value] * horizon
            residual_std = np.std(data) if len(data) > 1 else last_value * 0.1
        else:
            # Son 4 haftanın ağırlıklı ortalaması + eğilim
            weights = [0.4, 0.3, 0.2, 0.1]  # En son hafta en yüksek ağırlık
            weighted_avg = sum(data[-4:][i] * weights[i] for i in range(4))
            
            # Eğilim (son 4 haftanın eğimi)
            x = np.arange(4)
            y = data[-4:]
            slope = np.polyfit(x, y, 1)[0]
            
            forecast_mean = []
            for i in range(horizon):
                pred = weighted_avg + slope * (i + 1)
                forecast_mean.append(max(0, pred))  # Negatif tahmin olmasın
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
        
        # Model seçimi
        if model_type == "auto":
            model_type = self.auto_select_model(historical_data)
        
        # Tahmin yap
        if model_type == "holt_winters" and STATSMODELS_AVAILABLE:
            result = self.holt_winters_forecast(data, horizon)
        elif model_type == "arima" and STATSMODELS_AVAILABLE:
            result = self.arima_forecast(data, horizon)
        else:
            result = self.simple_forecast(historical_data, horizon)
        
        return result
    
    def get_forecast_accuracy(self, historical_data, test_horizon=4):
        """
        Forecast doğruluğunu test et (MAPE hesapla)
        historical_data: Tam veri (son test_horizon hafta test olarak kullanılacak)
        """
        if len(historical_data) < test_horizon + 8:
            return None
        
        train = historical_data[:-test_horizon]
        test = historical_data[-test_horizon:]
        
        forecast_result = self.forecast(train, horizon=test_horizon)
        forecast_mean = forecast_result['mean']
        
        # MAPE hesapla
        mape_values = []
        for actual, pred in zip(test, forecast_mean):
            if actual > 0:
                mape_values.append(abs((actual - pred) / actual) * 100)
        
        if mape_values:
            mape = np.mean(mape_values)
            return {
                'mape': round(mape, 2),
                'accuracy_level': 'YÜKSEK' if mape < 20 else ('ORTA' if mape < 40 else 'DÜŞÜK')
            }
        return None