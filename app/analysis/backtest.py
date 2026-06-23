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
                     unit_cost=100, test_window=12, 
                     strategies=None):
        """
        Backtest çalıştır.
        """
        if strategies is None:
            strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 
                         'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        
        if len(historical_demand) < test_window + 4:
            return {'error': f'Yetersiz veri: En az {test_window + 4} hafta gerekli'}
        
        test_start = len(historical_demand) - test_window
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
        
        # DataFrame oluştur
        df_results = pd.DataFrame(results).T
        
        # Eksik sütunları kontrol et ve doldur
        required_cols = ['service_level', 'total_holding_cost', 'total_shortage_cost', 
                        'total_cost', 'stockout_probability', 'total_shortage']
        for col in required_cols:
            if col not in df_results.columns:
                df_results[col] = 0
        
        df_results['total_cost'] = df_results['total_holding_cost'] + df_results['total_shortage_cost']
        df_results = df_results.sort_values('total_cost')
        
        best_strategy = df_results.index[0] if not df_results.empty else 'hybrid'
        
        # ✅ COMPARISON - TÜM METRİKLERİ EKLE
        comparison = {
            'service_level': df_results['service_level'].to_dict(),
            'total_cost': df_results['total_cost'].to_dict(),
            'total_holding_cost': df_results['total_holding_cost'].to_dict(),
            'total_shortage_cost': df_results['total_shortage_cost'].to_dict(),
            'stockout_probability': df_results['stockout_probability'].to_dict(),  # ✅ EKLENDİ
            'total_shortage': df_results['total_shortage'].to_dict()               # ✅ EKLENDİ
        }
        
        return {
            'metrics': results,
            'comparison': comparison,
            'recommendation': {
                'best_strategy': best_strategy,
                'reason': f'En düşük toplam maliyet ({df_results.loc[best_strategy, "total_cost"]:.0f} TL)'
            }
        }
    
    def _test_strategy(self, historical_demand, lead_time_days, test_window,
                      strategy, holding_cost_rate, shortage_cost, unit_cost):
        """Tek bir stratejiyi test eder."""
        test_start = len(historical_demand) - test_window
        weekly_ss = []
        weekly_stock_levels = []
        weekly_shortages = []
        
        daily_holding_cost = holding_cost_rate / 365
        daily_shortage_cost = shortage_cost
        
        for i in range(test_window):
            current_week = test_start + i
            train_data = historical_demand[:current_week]
             
            if len(train_data) < 4:
                train_data = historical_demand[max(0, current_week-8):current_week]
                if len(train_data) < 4:
                    train_data = [np.mean(historical_demand[:current_week+1])] * 4

            ss = self._calculate_safety_stock_by_strategy(train_data, lead_time_days, strategy)
            weekly_ss.append(ss)
            
            actual_demand = historical_demand[current_week]
            
            if i == 0:
                daily_demand = np.mean(train_data[-4:]) / self.days_per_week if len(train_data) >= 4 else actual_demand / self.days_per_week
                lead_time_demand = daily_demand * lead_time_days
                stock = ss + lead_time_demand
            else:
                stock = weekly_stock_levels[i-1]
            
            if stock >= actual_demand:
                stock -= actual_demand
                shortage = 0
            else:
                shortage = actual_demand - stock
                stock = 0
            
            weekly_stock_levels.append(stock)
            weekly_shortages.append(shortage)
        
        total_demand = sum(historical_demand[-test_window:])
        total_shortage = sum(weekly_shortages)
        
        avg_inventory = np.mean(weekly_stock_levels) if weekly_stock_levels else 0
        avg_inventory_value = avg_inventory * unit_cost
        
        total_holding_cost = avg_inventory_value * daily_holding_cost * (test_window * self.days_per_week)
        total_shortage_cost = total_shortage * daily_shortage_cost
        
        service_level = 1 - (total_shortage / total_demand) if total_demand > 0 else 1.0
        
        # ✅ STOK TÜKENME OLASILIĞI (Hafta bazında)
        stockout_weeks = sum(1 for s in weekly_shortages if s > 0)
        stockout_probability = stockout_weeks / test_window if test_window > 0 else 0
        
        # ✅ STRATEJİ SONUCU - TÜM METRİKLER
        return {
            'strategy': strategy,
            'service_level': round(service_level, 4),
            'stockout_probability': round(stockout_probability, 4),  # ✅ EKLENDİ
            'total_shortage': round(total_shortage, 2),              # ✅ EKLENDİ
            'total_shortage_cost': round(total_shortage_cost, 2),
            'total_holding_cost': round(total_holding_cost, 2),
            'total_cost': round(total_holding_cost + total_shortage_cost, 2),
            'avg_inventory': round(avg_inventory, 2)
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
            avg = np.mean(train_data[-4:]) if len(train_data) >= 4 else np.mean(train_data)
            lt_weeks = lead_time_days / 7
            return avg * lt_weeks * 0.3
        elif strategy == 'last_value':
            last = train_data[-1] if train_data else 0
            lt_weeks = lead_time_days / 7
            return last * lt_weeks * 0.2
        else:  # 'ai' veya varsayılan
            return self.ss_optimizer.hybrid_safety_stock(train_data, lead_time_days)