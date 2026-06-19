"""
Talep Pattern Analizi Modülü
EM_Stok.py'deki AdvancedDemandAnalyzer sınıfından taşınmıştır.
"""

import numpy as np


class AdvancedDemandAnalyzer:
    """Gelişmiş Talep Paterni Analiz Sınıfı"""

    def __init__(self, days_per_week=6):
        self.days_per_week = days_per_week

    def analyze_demand_pattern(self, weekly_data):
        """Talep paternini detaylı analiz et"""
        if not weekly_data:
            return "STANDART", {
                'cv': 0, 'zero_ratio': 0, 'trend': 0,
                'mean': 0, 'std': 0, 'median': 0
            }

        zero_count = weekly_data.count(0) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0)
        total_count = len(weekly_data)
        zero_ratio = zero_count / total_count if total_count > 0 else 0

        mean_val = np.mean(weekly_data)
        std_val = np.std(weekly_data)

        if mean_val > 0:
            cv = std_val / mean_val
        else:
            cv = 0

        # Eğer tüm değerler sıfırsa
        if mean_val == 0:
            pattern = "SIFIR_TALEP"
            pattern_stats = {
                'cv': 0,
                'zero_ratio': zero_ratio,
                'trend': 0,
                'mean': 0,
                'std': 0,
                'median': 0
            }
            return pattern, pattern_stats

        # Trend analizi
        trend = self._calculate_trend(weekly_data) if len(weekly_data) >= 4 else 0

        # Pattern belirleme
        pattern = self._determine_pattern(cv, zero_ratio, trend)

        pattern_stats = {
            'cv': cv,
            'zero_ratio': zero_ratio,
            'trend': trend,
            'mean': mean_val,
            'std': std_val,
            'median': np.median(weekly_data)
        }
        return pattern, pattern_stats

    def _calculate_trend(self, data):
        """Trend analizi (son 4+ haftanın eğimi)"""
        if len(data) < 2:
            return 0
        x = np.arange(len(data))
        y = np.array(data)
        try:
            slope, _ = np.polyfit(x, y, 1)
        except:
            return 0
        mean_y = np.mean(y)
        if mean_y > 0:
            trend_percentage = (slope * len(data)) / mean_y * 100
        else:
            trend_percentage = 0
        return trend_percentage

    def _determine_pattern(self, cv, zero_ratio, trend):
        """Pattern belirleme (Türkçe)"""
        # 1. Sıfır talep kontrolü
        if zero_ratio >= 0.875:  # 7/8 veya daha fazla sıfır
            return "SIFIR_TALEP"

        # 2. Aralıklı talep
        if zero_ratio > 0.5:
            return "ARALIKLI_YUKSEK" if cv > 1.5 else "ARALIKLI_DUSUK"

        # 3. Düzenli talep
        if cv < 0.3:
            if abs(trend) > 20:
                return "DUZENLI_ARTS" if trend > 0 else "DUZENLI_AZALIS"
            else:
                return "DUZENLI_SABIT"

        # 4. Değişken talep
        if cv < 0.7:
            return "DEGISKEN"
        if cv < 1.5:
            return "YUKSEK_DEGISKEN"
        return "ASIRI_DEGISKEN"