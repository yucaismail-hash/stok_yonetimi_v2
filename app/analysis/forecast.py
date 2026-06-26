"""
Talep Tahmini (Forecast) Modülü - Pattern Entegre
Desteklenen modeller: Holt-Winters, ARIMA, Basit Hareketli Ortalama
Pattern analizi ile model seçimi iyileştirilmiştir.
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
    """Talep Tahmin Sınıfı - Pattern ile zenginleştirilmiş"""
    
    def __init__(self, seasonal_periods=52):
        self.seasonal_periods = seasonal_periods
        self.model = None
        self.model_type = None
        self.fitted = False
        self._pattern_analyzer = None
    
    def set_pattern_analyzer(self, pattern_analyzer):
        """Pattern analizcisini ata"""
        self._pattern_analyzer = pattern_analyzer
    
    def get_pattern(self, historical_data: List[float]) -> Tuple[str, Dict]:
        """Verinin pattern'ini analiz et"""
        if self._pattern_analyzer:
            return self._pattern_analyzer.analyze_demand_pattern(historical_data)
        return "DEGISKEN", {'cv': 0.5, 'zero_ratio': 0, 'trend': 0, 'mean': 0, 'std': 0, 'median': 0}
    
    def auto_select_model(self, historical_data) -> Tuple[str, Dict]:
        """
        Otomatik model seçimi - Pattern bilgisi ile zenginleştirilmiş
        """
        n = len(historical_data)
        
        # ✅ Pattern analizi yap
        pattern, pattern_stats = self.get_pattern(historical_data)
        cv = pattern_stats.get('cv', 0)
        zero_ratio = pattern_stats.get('zero_ratio', 0)
        trend = pattern_stats.get('trend', 0)
        
        # Veri yetersizse basit dön
        if n < 8:
            return "simple", {
                "selection_reason": "Yetersiz veri, basit model kullanıldı",
                "pattern": pattern,
                "pattern_label": get_pattern_label(pattern)
            }
        
        # ✅ Pattern'e göre model önceliklendirme
        model_priority = []
        
        if pattern == 'SIFIR_TALEP':
            model_priority = ['simple']
        elif pattern in ['DUZENLI_SABIT', 'DUZENLI_ARTS', 'DUZENLI_AZALIS']:
            if STATSMODELS_AVAILABLE and n >= 12:
                model_priority = ['holt_winters', 'arima', 'simple']
            else:
                model_priority = ['arima', 'simple']
        elif pattern in ['ARALIKLI_DUSUK', 'ARALIKLI_YUKSEK']:
            # Aralıklı talep için basit model daha iyi
            model_priority = ['simple', 'arima']
        elif pattern in ['DEGISKEN', 'YUKSEK_DEGISKEN']:
            if STATSMODELS_AVAILABLE and n >= 13:
                model_priority = ['arima', 'holt_winters', 'simple']
            else:
                model_priority = ['arima', 'simple']
        elif pattern == 'ASIRI_DEGISKEN':
            model_priority = ['simple', 'arima']
        else:
            model_priority = ['simple', 'arima', 'holt_winters']
        
        # ✅ Mevsimsellik kontrolü
        seasonal_periods = self.detect_seasonality(historical_data)
        
        # Walk-Forward Validation
        test_size = min(4, n // 4)
        if test_size < 2:
            test_size = 2
        
        best_mape = float('inf')
        best_model = 'simple'
        scores = {}
        
        for model_name in model_priority:
            mape_list = []
            
            for i in range(test_size, n - test_size + 1):
                train = historical_data[:i]
                test = historical_data[i:i+test_size]
                
                try:
                    if model_name == 'holt_winters':
                        result = self.holt_winters_forecast(train, horizon=test_size, seasonal_periods=seasonal_periods)
                    elif model_name == 'arima':
                        result = self.arima_forecast(train, horizon=test_size)
                    else:
                        result = self.simple_forecast(train, horizon=test_size)
                    
                    pred = result.get('mean', [])
                    if not pred:
                        continue
                    
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
            "selection_method": "Pattern + Walk-Forward CV",
            "models_tested": len(scores),
            "best_model": best_model,
            "best_mape": round(best_mape, 2) if best_mape != float('inf') else 999,
            "model_scores": {k: round(v, 2) for k, v in scores.items()},
            "selection_reason": f"Pattern: {get_pattern_label(pattern)}, En düşük MAPE ile '{best_model}' seçildi",
            "pattern": pattern,
            "pattern_label": get_pattern_label(pattern),
            "cv": round(cv, 4),
            "zero_ratio": round(zero_ratio, 4),
            "trend": round(trend, 2)
        }
        
        return best_model, selection_info

    def detect_seasonality(self, data: List[float]) -> int:
        """Verideki mevsimselliği otomatik tespit et"""
        n = len(data)
        if n < 12:
            return min(4, n // 2)
        
        try:
            # FFT ile frekans analizi
            fft = np.fft.fft(data)
            freqs = np.fft.fftfreq(len(data))
            power = np.abs(fft) ** 2
            power[0] = 0
            
            if len(power) > 1:
                max_freq_idx = np.argmax(power[1:]) + 1
                if max_freq_idx < len(freqs):
                    period = int(1 / abs(freqs[max_freq_idx]))
                    if 4 <= period <= 52:
                        return period
        except:
            pass
        
        return min(52, max(4, n // 4))

    def holt_winters_forecast(self, data, horizon=13, seasonal_periods=None):
        """Holt-Winters Mevsimsel Model ile Tahmin"""
        n = len(data)
        
        if seasonal_periods is None:
            seasonal_periods = min(self.seasonal_periods, max(4, n // 4))
        
        seasonal_periods = max(2, min(seasonal_periods, n // 2))
        
        if n < 8 or n < seasonal_periods * 2:
            return self.simple_forecast(data, horizon)
        
        try:
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
            
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
                'model_used': 'holt_winters',
                'seasonal_periods': seasonal_periods
            }
        except Exception as e:
            print(f"⚠️ Holt-Winters hatası: {e}")
            return self.simple_forecast(data, horizon)

    def arima_forecast(self, data, horizon=13, order=(1,1,1)):
        """ARIMA Modeli ile Tahmin"""
        n = len(data)
        
        if n < 8:
            return self.simple_forecast(data, horizon)
        
        try:
            best_aic = float('inf')
            best_order = order
            
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
                'model_used': 'arima',
                'order': best_order
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
        """Ana forecast fonksiyonu - Pattern ile zenginleştirilmiş"""
        if not historical_data or len(historical_data) < 4:
            raise ValueError("Yetersiz veri: En az 4 haftalık veri gerekli")
        
        selection_info = {}
        
        if model_type == "auto":
            model_type, selection_info = self.auto_select_model(historical_data)
        
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