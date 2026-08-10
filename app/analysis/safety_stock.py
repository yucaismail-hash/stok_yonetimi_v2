"""
Safety Stock (Emniyet Stoku) Optimizasyon Modülü - DÜZELTİLMİŞ (Recursion hatası yok)
"""

import numpy as np
from scipy import stats

class ComprehensiveSafetyStockOptimizer:
    """Kapsamlı Emniyet Stoku Optimizasyon Sınıfı"""

    def __init__(self, days_per_week=6):
        self.days_per_week = days_per_week

    # ==================== YARDIMCI METODLAR ====================
    def calculate_daily_stats(self, weekly_data):
        """Günlük istatistikleri hesapla"""
        daily_demands = []
        for week_demand in weekly_data:
            daily_demand = week_demand / self.days_per_week
            daily_demands.extend([daily_demand] * self.days_per_week)

        if len(daily_demands) < 2:
            return 0, 0

        daily_mean = np.mean(daily_demands)
        daily_std = np.std(daily_demands)
        return daily_mean, daily_std

    # ==================== 1. CLASSIC ====================
    def classic_safety_stock(self, weekly_data, lead_time_days, service_level=0.95):
        """Klasik emniyet stoğu formülü"""
        daily_mean, daily_std = self.calculate_daily_stats(weekly_data)
        if daily_mean <= 0:
            return 0

        z_score = stats.norm.ppf(service_level)
        ss = z_score * daily_std * np.sqrt(lead_time_days)

        min_ss = daily_mean * 1
        max_ss = daily_mean * lead_time_days
        return max(min_ss, min(ss, max_ss))

    # ==================== 2. CROSTON ====================
    def croston_method(self, weekly_data, lead_time_days, service_level=0.95):
        """Croston metodu (intermittent demand / aralıklı talep)"""
        zero_ratio = weekly_data.count(0) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0) / len(weekly_data)

        if zero_ratio < 0.5:
            return self.classic_safety_stock(weekly_data, lead_time_days, service_level)

        positive_weeks = [x for x in weekly_data if x > 0]
        if len(positive_weeks) == 0:
            return 0

        avg_demand_size = np.mean(positive_weeks)

        intervals = []
        last_positive = -1
        for i, demand in enumerate(weekly_data):
            if demand > 0:
                if last_positive != -1:
                    intervals.append(i - last_positive)
                last_positive = i

        avg_interval_weeks = np.mean(intervals) if intervals else len(weekly_data) / len(positive_weeks)
        weekly_demand_avg = avg_demand_size / avg_interval_weeks if avg_interval_weeks > 0 else 0
        daily_demand_avg = weekly_demand_avg / self.days_per_week
        daily_std = np.std([x / self.days_per_week for x in weekly_data])

        z_score = stats.norm.ppf(service_level)
        ss = z_score * daily_std * np.sqrt(lead_time_days)

        min_ss = daily_demand_avg * 1
        max_ss = daily_demand_avg * lead_time_days
        return max(min_ss, min(ss, max_ss)) if daily_demand_avg > 0 else 0

    # ==================== 3. SYNTETOS-BOYLAN ====================
    def syntetos_boylan_method(self, weekly_data, lead_time_days, service_level=0.95):
        """Syntetos-Boylan metodu"""
        zero_ratio = weekly_data.count(0) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0) / len(weekly_data)

        if zero_ratio < 0.5:
            return self.classic_safety_stock(weekly_data, lead_time_days, service_level)

        croston_ss = self.croston_method(weekly_data, lead_time_days, service_level)

        positive_weeks = [x for x in weekly_data if x > 0]
        n = len(positive_weeks)
        if n == 0:
            return 0

        correction_factor = 1 - (0.18 / n) if n > 0 else 1
        sb_ss = croston_ss * correction_factor

        daily_mean, _ = self.calculate_daily_stats(weekly_data)
        min_ss = daily_mean * 1 if daily_mean > 0 else 0
        max_ss = daily_mean * lead_time_days if daily_mean > 0 else 0
        return max(min_ss, min(sb_ss, max_ss)) if daily_mean > 0 else 0

    # ==================== 4. BOOTSTRAPPING ====================
    def bootstrapping_method(self, weekly_data, lead_time_days, service_level=0.95, n_iterations=2000):
        """Bootstrap simülasyonu"""
        daily_demands = []
        for week_demand in weekly_data:
            daily_demand = week_demand / self.days_per_week
            daily_demands.extend([daily_demand] * self.days_per_week)

        if len(daily_demands) < lead_time_days * 2:
            return self.classic_safety_stock(weekly_data, lead_time_days, service_level)

        simulations = []
        for _ in range(min(n_iterations, 1000)):  # max 1000 iterasyon
            sample = np.random.choice(daily_demands, size=lead_time_days, replace=True)
            total_demand = np.sum(sample)
            simulations.append(total_demand)

        simulations.sort()
        index = int((1 - service_level) * len(simulations))
        safety_stock = max(0, simulations[index] - np.mean(simulations))

        daily_mean, _ = self.calculate_daily_stats(weekly_data)
        min_ss = daily_mean * 1 if daily_mean > 0 else 0
        max_ss = daily_mean * lead_time_days if daily_mean > 0 else 0
        return max(min_ss, min(safety_stock, max_ss)) if daily_mean > 0 else 0

    # ==================== 5. MAKİNE ÖĞRENMESİ ====================
    def ml_based_safety_stock(self, weekly_data, lead_time_days, service_level=0.95):
        """Makine öğrenmesi tabanlı emniyet stoku"""
        if len(weekly_data) < 8:
            return self.classic_safety_stock(weekly_data, lead_time_days, service_level)

        non_zero = [x for x in weekly_data if x > 0]
        if len(non_zero) == 0:
            return 0

        mean_val = np.mean(non_zero)
        std_val = np.std(non_zero)
        cv = std_val / mean_val if mean_val > 0 else 0
        zero_ratio = weekly_data.count(0) / len(weekly_data) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0) / len(weekly_data)

        # Trend
        x = np.arange(len(weekly_data))
        y = np.array(weekly_data)
        try:
            slope, _ = np.polyfit(x, y, 1)
            trend = (slope * len(weekly_data)) / mean_val * 100 if mean_val > 0 else 0
        except:
            trend = 0

        daily_mean, _ = self.calculate_daily_stats(weekly_data)

        base_ss = daily_mean * lead_time_days * 0.3
        cv_factor = 1 + cv * 1.5
        zero_factor = 1 + zero_ratio * 2
        trend_factor = 1 + abs(trend) / 200
        service_factor = stats.norm.ppf(service_level) / 1.645

        ml_ss = base_ss * cv_factor * zero_factor * trend_factor * service_factor

        min_ss = daily_mean * 1
        max_ss = daily_mean * lead_time_days
        return max(min_ss, min(ml_ss, max_ss))

    # ==================== 6. HİBRİT (Kendi kendini çağırmıyor) ====================
    def hybrid_safety_stock(self, weekly_data, lead_time_days, service_level=0.95):
        """Hibrit emniyet stoku - DOĞRUDAN HESAPLAMA, kendini çağırmaz"""
        zero_ratio = weekly_data.count(0) / len(weekly_data) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0) / len(weekly_data)

        # Doğrudan hesapla (calculate_all_methods'e gerek yok)
        classic = self.classic_safety_stock(weekly_data, lead_time_days, service_level)
        croston = self.croston_method(weekly_data, lead_time_days, service_level)
        sb = self.syntetos_boylan_method(weekly_data, lead_time_days, service_level)
        ml = self.ml_based_safety_stock(weekly_data, lead_time_days, service_level)

        if zero_ratio > 0.5:
            # Aralıklı talep: Croston ve SB daha ağırlıklı
            hybrid = classic * 0.1 + croston * 0.4 + sb * 0.4 + ml * 0.1
        else:
            # Sürekli talep: Classic ve ML daha ağırlıklı
            hybrid = classic * 0.4 + croston * 0.1 + sb * 0.1 + ml * 0.4

        daily_mean, _ = self.calculate_daily_stats(weekly_data)
        min_ss = daily_mean * 1 if daily_mean > 0 else 0
        max_ss = daily_mean * lead_time_days if daily_mean > 0 else 0

        return max(min_ss, min(hybrid, max_ss)) if daily_mean > 0 else 0

    def _hybrid_from_candidates(self, weekly_data, lead_time_days, classic, croston, sb, ml):
        """Combine already-computed candidates without recalculating them."""
        zero_ratio = weekly_data.count(0) / len(weekly_data) if isinstance(weekly_data, list) else np.sum(np.array(weekly_data) == 0) / len(weekly_data)
        if zero_ratio > 0.5:
            hybrid = classic * 0.1 + croston * 0.4 + sb * 0.4 + ml * 0.1
        else:
            hybrid = classic * 0.4 + croston * 0.1 + sb * 0.1 + ml * 0.4
        daily_mean, _ = self.calculate_daily_stats(weekly_data)
        min_ss = daily_mean if daily_mean > 0 else 0
        max_ss = daily_mean * lead_time_days if daily_mean > 0 else 0
        return max(min_ss, min(hybrid, max_ss)) if daily_mean > 0 else 0

    # ==================== TOPLU HESAPLAMA (Recursion yok) ====================
    def calculate_all_methods(self, weekly_data, lead_time_days, service_level=0.95):
        """Tüm metodları hesapla - Kendi kendini çağırmaz"""
        try:
            classic = self.classic_safety_stock(weekly_data, lead_time_days, service_level)
            croston = self.croston_method(weekly_data, lead_time_days, service_level)
            syntetos = self.syntetos_boylan_method(weekly_data, lead_time_days, service_level)
            bootstrap = self.bootstrapping_method(weekly_data, lead_time_days, service_level)
            ml = self.ml_based_safety_stock(weekly_data, lead_time_days, service_level)
            hybrid = self._hybrid_from_candidates(weekly_data, lead_time_days, classic, croston, syntetos, ml)

            return {
                'classic_ss': round(classic, 2),
                'croston_ss': round(croston, 2),
                'syntetos_boylan_ss': round(syntetos, 2),
                'bootstrapping_ss': round(bootstrap, 2),
                'ml_ss': round(ml, 2),
                'hybrid_ss': round(hybrid, 2)
            }
        except Exception as e:
            print(f"[ERROR] SS hesaplama hatası: {e}")
            return {
                'classic_ss': 0, 'croston_ss': 0, 'syntetos_boylan_ss': 0,
                'bootstrapping_ss': 0, 'ml_ss': 0, 'hybrid_ss': 0
            }
