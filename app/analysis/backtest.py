"""
Backtest Modülü - Geçmiş veri üzerinde strateji karşılaştırması
"""

import numpy as np
import pandas as pd
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.pattern import AdvancedDemandAnalyzer

class BacktestEngine:
    """Stok stratejilerini geçmiş veri üzerinde test eder"""
    
    def __init__(self, days_per_week=6):
        self.days_per_week = days_per_week
        self.ss_optimizer = ComprehensiveSafetyStockOptimizer(days_per_week)
        self.pattern_analyzer = AdvancedDemandAnalyzer(days_per_week)
    
    def run_backtest(self, historical_demand, lead_time_days, 
                     holding_cost_rate=0.20, shortage_cost=500, 
                     unit_cost=100, test_window=26, 
                     strategies=None):
        """
        Backtest çalıştır.
        
        Args:
            historical_demand: List[float] - Haftalık talep (en az 52 hafta önerilir)
            lead_time_days: int - Tedarik süresi (gün)
            holding_cost_rate: float - Stok tutma maliyeti oranı (yıllık, 0.20 = %20)
            shortage_cost: float - Birim stok tükenme maliyeti
            unit_cost: float - Birim maliyet
            test_window: int - Kaç hafta test edilecek (son test_window hafta)
            strategies: List[str] - Test edilecek stratejiler (None = hepsi)
        
        Returns:
            dict: Her strateji için metrikler ve sıralama
        """
        if strategies is None:
            strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 
                         'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        
        if len(historical_demand) < test_window + 12:
            return {'error': f'Yetersiz veri: En az {test_window + 12} hafta gerekli'}
        
        # Test dönemi (son test_window hafta)
        test_start = len(historical_demand) - test_window
        train_end = test_start  # Eğitim verisi test döneminden önceki tüm veriler
        
        results = {}
        
        for strategy in strategies:
            metrics = self._test_strategy(
                historical_demand=historical_demand,
                lead_time_days=lead_time_days,
                test_window=test_window,
                strategy=strategy,
                holding_cost_rate=holding_cost_rate,
                shortage_cost=shortage_cost,
                unit_cost=unit_cost
            )
            results[strategy] = metrics
        
        # Sonuçları karşılaştır ve sırala
        df_results = pd.DataFrame(results).T
        df_results['total_cost'] = df_results['total_holding_cost'] + df_results['total_shortage_cost']
        df_results = df_results.sort_values('total_cost')
        
        best_strategy = df_results.index[0]
        recommendation = {
            'best_strategy': best_strategy,
            'reason': f'En düşük toplam maliyet ({df_results.loc[best_strategy, "total_cost"]:.0f} TL)',
            'ranking': df_results[['service_level', 'total_cost']].to_dict()
        }
        
        return {
            'metrics': results,
            'summary': {
                'test_weeks': test_window,
                'total_demand': sum(historical_demand[-test_window:]),
                'avg_weekly_demand': np.mean(historical_demand[-test_window:]),
                'demand_volatility': np.std(historical_demand[-test_window:]) / (np.mean(historical_demand[-test_window:]) + 1e-10)
            },
            'comparison': df_results[['service_level', 'total_holding_cost', 
                                      'total_shortage_cost', 'total_cost']].to_dict(),
            'recommendation': recommendation
        }
    
    def _test_strategy(self, historical_demand, lead_time_days, test_window,
                      strategy, holding_cost_rate, shortage_cost, unit_cost):
        """
        Tek bir stratejiyi test eder.
        Rolling window yaklaşımı: Her test haftası için, o haftadan önceki verilerle SS hesapla.
        """
        test_start = len(historical_demand) - test_window
        weekly_ss = []
        weekly_stock_levels = []
        weekly_shortages = []
        
        # Günlük istatistikler
        daily_holding_cost = holding_cost_rate / 365  # Günlük tutma maliyeti
        daily_shortage_cost = shortage_cost  # Birim stok tükenme maliyeti
        
        for i in range(test_window):
            # O anki hafta indeksi (test_start + i)
            current_week = test_start + i
            # Eğitim verisi: current_week'e kadar olan tüm veri (en az 4 hafta)
            train_data = historical_demand[:current_week]
             
            if len(train_data) < 4:
                train_data = historical_demand[max(0, current_week-8):current_week] # Fallback
                if len(train_data) < 4:
                    train_data = [np.mean(historical_demand[:current_week+1])] * 4


            # Emniyet stoğu hesapla
            ss = self._calculate_safety_stock_by_strategy(train_data, lead_time_days, strategy)
            weekly_ss.append(ss)
            
            # Gerçek talep (test haftasında)
            actual_demand = historical_demand[current_week]
            
            # Basit stok takibi: Bu hafta başı stok = bir önceki hafta sonu stok + (sipariş geldiyse)
            if i == 0:
                # İlk hafta: stok seviyesi = SS + lead_time_demand (tahmini)
                daily_demand = np.mean(train_data[-4:]) / self.days_per_week if len(train_data) >= 4 else actual_demand / self.days_per_week
                lead_time_demand = daily_demand * lead_time_days
                stock = ss + lead_time_demand
            else:
                stock = weekly_stock_levels[i-1]  # Geçen hafta sonu stok
            
            # Stok tüketimi
            if stock >= actual_demand:
                stock -= actual_demand
                shortage = 0
            else:
                shortage = actual_demand - stock
                stock = 0
            
            weekly_stock_levels.append(stock)
            weekly_shortages.append(shortage)
        
        # Metrikleri hesapla
        total_demand = sum(historical_demand[-test_window:])
        total_shortage = sum(weekly_shortages)
        
        # Ortalama stok seviyesi (TL cinsinden)
        avg_inventory = np.mean(weekly_stock_levels)
        avg_inventory_value = avg_inventory * unit_cost
        
        # Toplam tutma maliyeti (günlük * gün sayısı)
        total_holding_cost = avg_inventory_value * daily_holding_cost * (test_window * self.days_per_week)
        
        # Toplam stok tükenme maliyeti
        total_shortage_cost = total_shortage * daily_shortage_cost
        
        # Servis seviyesi (talebin karşılanma oranı)
        service_level = 1 - (total_shortage / total_demand) if total_demand > 0 else 1.0
        
        # Stok tükenme olasılığı (hafta bazında)
        stockout_weeks = sum(1 for s in weekly_shortages if s > 0)
        stockout_probability = stockout_weeks / test_window
        
        return {
            'strategy': strategy,
            'service_level': round(service_level, 4),
            'stockout_probability': round(stockout_probability, 4),
            'total_shortage': round(total_shortage, 2),
            'avg_inventory': round(avg_inventory, 2),
            'avg_inventory_value': round(avg_inventory_value, 2),
            'total_holding_cost': round(total_holding_cost, 2),
            'total_shortage_cost': round(total_shortage_cost, 2),
            'total_cost': round(total_holding_cost + total_shortage_cost, 2)
        }
    
    def _calculate_safety_stock_by_strategy(self, train_data, lead_time_days, strategy):
        """Strateji adına göre SS hesapla"""
        
        if lead_time_days <= 0:
            return 0
        if len(train_data) == 0:
            return 0
        
        if strategy == 'classic':
            return self.ss_optimizer.classic_safety_stock(train_data, lead_time_days)
        elif strategy == 'croston':
            return self.ss_optimizer.croston_method(train_data, lead_time_days)
        elif strategy == 'syntetos_boylan':
            return self.ss_optimizer.syntetos_boylan_method(train_data, lead_time_days)
        elif strategy == 'ml':
            return self.ss_optimizer.ml_based_safety_stock(train_data, lead_time_days)
        elif strategy == 'hybrid':
            return self.ss_optimizer.hybrid_safety_stock(train_data, lead_time_days)
        elif strategy == 'simple_moving_avg':
            # Basit: son 4 haftanın ortalaması * lead_time_in_weeks * 0.3
            avg = np.mean(train_data[-4:]) if len(train_data) >= 4 else np.mean(train_data)
            lt_weeks = lead_time_days / 7
            return avg * lt_weeks * 0.3
        elif strategy == 'last_value':
            # Son değer * lead_time_in_weeks * 0.2
            last = train_data[-1] if train_data else 0
            lt_weeks = lead_time_days / 7
            return last * lt_weeks * 0.2
        else:  # 'ai' veya varsayılan
            # AI = hybrid + pattern multiplier (basit hybrid şimdilik)
            return self.ss_optimizer.hybrid_safety_stock(train_data, lead_time_days)