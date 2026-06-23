"""
Monte Carlo Stok Simülasyonu Modülü - Gelişmiş Modüller Seçimli
Seçenekler: Rejim (Regime), Copula, Adaptive SS
"""

import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

class MonteCarloInventorySimulator:
    """
    Gelişmiş Monte Carlo Simülatörü (Rejim, Copula, Adaptive SS seçimli)
    """
    
    def __init__(self, n_simulations=1000):
        self.n_simulations = n_simulations
        self._regime_ready = False
        self._regime_params = None
        self._regime_trans = None
    
    # ==================== REJİM MODÜLÜ (Basit 2-rejim) ====================
    def _fit_regime_model(self, historical_demand):
        """Basit 2-rejim: LOW/HIGH (median bazlı) - 12 hafta yeterli"""
        hist = np.array(historical_demand)
        if len(hist) < 12:
            print(f"⚠️ Rejim için yetersiz veri: {len(hist)} hafta")
            self._regime_ready = False
            return
        
        med = np.median(hist)
        low = hist[hist <= med]
        high = hist[hist > med]
        
        low_mean = np.mean(low) if len(low) > 0 else np.mean(hist)
        low_std = np.std(low) if len(low) > 0 else np.std(hist) * 0.5
        high_mean = np.mean(high) if len(high) > 0 else np.mean(hist)
        high_std = np.std(high) if len(high) > 0 else np.std(hist) * 1.5
        
        self._regime_params = {
            'low': (max(0.1, low_mean), max(0.01, low_std)),
            'high': (max(0.1, high_mean), max(0.01, high_std))
        }
        self._regime_trans = np.array([[0.85, 0.15], [0.20, 0.80]])
        self._regime_ready = True
        print(f"✅ Rejim modeli hazır: Low={low_mean:.1f}, High={high_mean:.1f}")
    
    def _sample_regime(self, prev_regime):
        if not self._regime_ready:
            return prev_regime
        u = np.random.random()
        return 0 if u < self._regime_trans[prev_regime][0] else 1
    
    # ==================== COPULA MODÜLÜ (Sabit korelasyon) ====================
    @staticmethod
    def _get_conditional_leadtime(demand_percentile, correlation=0.7, lt_mean=14, lt_std=3):
        """Talebe bağlı koşullu lead time (Copula benzeri)"""
        demand_percentile = max(0.01, min(0.99, demand_percentile))
        z_demand = stats.norm.ppf(demand_percentile)
        conditional_mean = correlation * z_demand
        conditional_var = 1 - correlation**2
        normal_sample = np.random.normal(conditional_mean, np.sqrt(conditional_var))
        normal_sample = max(-3, min(3, normal_sample))
        v_conditional = stats.norm.cdf(normal_sample)
        v_conditional = max(0.001, min(0.999, v_conditional))
        mu = np.log(lt_mean**2 / np.sqrt(lt_std**2 + lt_mean**2))
        sigma = np.sqrt(np.log(1 + (lt_std**2 / lt_mean**2)))
        leadtime = stats.lognorm.ppf(v_conditional, s=sigma, scale=np.exp(mu))
        return max(1, min(365, leadtime))
    
    # ==================== ANA SİMÜLASYON (Seçimli) ====================
    def simulate(self, initial_stock, lead_time_mean, lead_time_std,
                 demand_mean, demand_std, eoq, rop, weeks=26,
                 lead_time_dist='lognormal',
                 use_regime=False, historical_demand=None,
                 use_copula=False, correlation=0.7,
                 use_adaptive_ss=False, target_service=0.95,
                 review_period=4, inc_rate=0.08, dec_rate=0.03):
        """
        Monte Carlo simülasyonu - Gelişmiş modüller seçimli.
        """
        n_sim = self.n_simulations
        
        # ✅ Rejim modelini hazırla (12 hafta yeterli)
        regime_used = False
        if use_regime and historical_demand and len(historical_demand) >= 12:
            self._fit_regime_model(historical_demand)
            regime_used = True
            print(f"✅ Rejim modeli aktif: {len(historical_demand)} hafta veri ile")
        elif use_regime and historical_demand:
            self._fit_regime_model(historical_demand)
            regime_used = True
            print(f"⚠️ Rejim modeli aktif (az veri): {len(historical_demand)} hafta ile")
        
        # Sonuç matrisleri
        stock_paths = np.zeros((n_sim, weeks))
        order_paths = np.zeros((n_sim, weeks))
        shortage_paths = np.zeros((n_sim, weeks))
        
        for sim in range(n_sim):
            stock = initial_stock
            open_orders = {}
            regime_state = 0
            rop_current = rop
            
            recent_stockout_flags = []
            recent_demand = []
            
            for week in range(weeks):
                # Açık siparişleri al
                if week in open_orders:
                    stock += open_orders[week]
                    del open_orders[week]
                
                # ---- TALEP ÜRETİMİ (Rejimli veya normal) ----
                if use_regime and regime_used and self._regime_ready:
                    regime_state = self._sample_regime(regime_state)
                    mean_d = self._regime_params['low' if regime_state == 0 else 'high'][0]
                    std_d = self._regime_params['low' if regime_state == 0 else 'high'][1]
                else:
                    mean_d = demand_mean
                    std_d = demand_std
                
                if mean_d > 0:
                    mu = np.log(mean_d**2 / np.sqrt(std_d**2 + mean_d**2))
                    sigma = np.sqrt(np.log(1 + (std_d**2 / mean_d**2)))
                    demand = np.random.lognormal(mu, sigma)
                else:
                    demand = 0
                
                if np.random.random() < 0.1:
                    demand = 0
                
                # Stok tüketimi
                if stock >= demand:
                    stock -= demand
                    shortage = 0
                    stockout_flag = 0
                else:
                    shortage = demand - stock
                    stock = 0
                    stockout_flag = 1
                
                shortage_paths[sim, week] = shortage
                stock_paths[sim, week] = stock
                
                # ---- ADAPTIVE SS GÜNCELLEME ----
                if use_adaptive_ss:
                    recent_stockout_flags.append(stockout_flag)
                    recent_demand.append(demand)
                    if len(recent_stockout_flags) > review_period:
                        recent_stockout_flags.pop(0)
                        recent_demand.pop(0)
                    
                    if (week + 1) % review_period == 0 and len(recent_stockout_flags) == review_period:
                        window_service = 1.0 - (sum(recent_stockout_flags) / review_period)
                        if window_service < target_service:
                            rop_current = rop_current * (1.0 + inc_rate)
                        elif window_service > min(0.999, target_service + 0.03):
                            rop_current = rop_current * (1.0 - dec_rate)
                        rop_current = max(rop * 0.5, min(rop * 2.0, rop_current))
                
                # ---- SİPARİŞ KARARI ----
                if stock + sum(open_orders.values()) < rop_current:
                    order_qty = eoq
                    
                    if use_copula:
                        if historical_demand:
                            percentile = np.sum(np.array(historical_demand) <= demand) / len(historical_demand)
                        else:
                            percentile = 0.5
                        lt_days = self._get_conditional_leadtime(percentile, correlation,
                                                                 lead_time_mean, lead_time_std)
                    else:
                        if lead_time_dist == 'normal':
                            lt_days = np.random.normal(lead_time_mean, lead_time_std)
                        else:
                            mu_lt = np.log(lead_time_mean**2 / np.sqrt(lead_time_std**2 + lead_time_mean**2))
                            sigma_lt = np.sqrt(np.log(1 + (lead_time_std**2 / lead_time_mean**2)))
                            lt_days = np.random.lognormal(mu_lt, sigma_lt)
                    
                    lt_days = max(1, lt_days)
                    lt_weeks = lt_days / 7.0
                    arrival_week = week + int(np.ceil(lt_weeks))
                    if arrival_week < weeks:
                        open_orders[arrival_week] = open_orders.get(arrival_week, 0) + order_qty
                    order_paths[sim, week] = order_qty
                else:
                    order_paths[sim, week] = 0
        
        # İstatistikler
        service_level = 1 - (np.sum(shortage_paths > 0) / (n_sim * weeks))
        total_shortages = np.sum(shortage_paths, axis=1)
        sorted_shortages = np.sort(total_shortages)
        cvar_95 = np.mean(sorted_shortages[int(0.95 * n_sim):]) if n_sim > 0 else 0
        
        return {
            'stock_paths': stock_paths.tolist(),
            'order_paths': order_paths.tolist(),
            'shortage_paths': shortage_paths.tolist(),
            'avg_stock': np.mean(stock_paths, axis=0).tolist(),
            'std_stock': np.std(stock_paths, axis=0).tolist(),
            'avg_orders': np.mean(order_paths, axis=0).tolist(),
            'stockout_probability': (np.mean(shortage_paths > 0, axis=0)).tolist(),
            'expected_shortage': np.mean(shortage_paths, axis=0).tolist(),
            'service_level': float(service_level),
            'cvar_95': float(cvar_95),
            'regime_used': regime_used,
            'copula_used': use_copula,
            'adaptive_ss_used': use_adaptive_ss
        }