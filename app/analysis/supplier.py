"""
Tedarikçi Analiz ve Optimizasyon Modülü
Sim_Stok_Core.py'deki SupplierPerformanceAnalyzer ve optimize_supplier_shares kodlarından taşınmıştır.
"""

import numpy as np
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

class SupplierPerformanceAnalyzer:
    """Tedarikçi Performans Analiz Sistemi"""
    
    def __init__(self):
        self.supplier_data = defaultdict(lambda: {
            'delivery_history': [],
            'quality_history': [],
            'lead_time_history': [],
            'risk_score': 0.5,
            'performance_score': 0.5,
            'supplier_factor': 1.0
        })
    
    def add_delivery_record(self, supplier_id: str, planned_date: datetime, actual_date: datetime,
                           planned_qty: float, actual_qty: float, defects: int = 0):
        """Teslimat kaydı ekle"""
        delay_days = max(0, (actual_date - planned_date).days)
        qty_compliance = min(1.0, actual_qty / planned_qty) if planned_qty > 0 else 1.0
        quality_rate = 1.0 - (defects / (actual_qty + 1e-10))
        
        record = {
            'date': actual_date,
            'delay_days': delay_days,
            'qty_compliance': qty_compliance,
            'quality_rate': quality_rate,
            'planned_qty': planned_qty,
            'actual_qty': actual_qty
        }
        
        self.supplier_data[supplier_id]['delivery_history'].append(record)
        self._update_scores(supplier_id)
    
    def _update_scores(self, supplier_id: str):
        """Risk ve performans skorlarını güncelle"""
        history = self.supplier_data[supplier_id]['delivery_history']
        
        if not history:
            return
        
        recent = history[-20:]
        avg_delay = np.mean([r['delay_days'] for r in recent])
        avg_qty_compliance = np.mean([r['qty_compliance'] for r in recent])
        avg_quality = np.mean([r['quality_rate'] for r in recent])
        
        delay_std = np.std([r['delay_days'] for r in recent])
        delay_cv = delay_std / (avg_delay + 1e-10)
        
        risk_score = (avg_delay / 14 + (1 - avg_qty_compliance) + (1 - avg_quality) + delay_cv) / 4
        perf_score = (avg_qty_compliance + avg_quality + (1 - min(1.0, avg_delay/7))) / 3
        
        self.supplier_data[supplier_id]['risk_score'] = min(1.0, max(0.0, risk_score))
        self.supplier_data[supplier_id]['performance_score'] = min(1.0, max(0.0, perf_score))
    
    def get_supplier_lead_time_distribution(self, supplier_id: str, demand_level: Optional[str] = None) -> Dict:
        """Talebe bağlı lead time dağılımı"""
        base_data = self.supplier_data[supplier_id]
        
        if not base_data['delivery_history']:
            return {'mean': 14, 'std': 3, 'distribution': 'normal', 'risk_score': 0.5, 'perf_score': 0.5}
        
        lead_times = [r['delay_days'] + 14 for r in base_data['delivery_history']]
        mean_lt = np.mean(lead_times)
        std_lt = np.std(lead_times)
        
        if demand_level == 'high':
            mean_lt *= 1.5
            std_lt *= 1.8
        elif demand_level == 'low':
            mean_lt *= 0.8
            std_lt *= 0.9
        
        return {
            'mean': max(7, min(60, mean_lt)),
            'std': max(1, min(20, std_lt)),
            'distribution': 'lognormal' if std_lt/mean_lt > 0.5 else 'normal',
            'risk_score': base_data['risk_score'],
            'perf_score': base_data['performance_score'],
            'supplier_factor': base_data.get('supplier_factor', 1.0)
        }
    
    def get_supplier_risk_score(self, supplier_id: str) -> float:
        """Tedarikçi risk skorunu getir (0-1, 1 en riskli)"""
        return self.supplier_data[supplier_id]['risk_score']
    
    def get_supplier_performance_score(self, supplier_id: str) -> float:
        """Tedarikçi performans skorunu getir (0-1, 1 en iyi)"""
        return self.supplier_data[supplier_id]['performance_score']


class SupplierShareOptimizer:
    """Tedarikçi Payı Optimizasyonu"""
    
    def __init__(self, supplier_analyzer: SupplierPerformanceAnalyzer):
        self.supplier_analyzer = supplier_analyzer
    
    def get_supplier_unit_cost(self, supplier_id: str, material: Dict, default_cost: float = 100.0) -> float:
        """Tedariçinin birim maliyetini getir"""
        # Öncelik sırası: material.suppliers[] -> supplier_data -> material.unit_cost
        for s in material.get("suppliers", []):
            if str(s.get("supplier_id")) == str(supplier_id):
                uc = s.get("unit_cost", None)
                if uc is not None:
                    return float(uc)
        
        sup_data = self.supplier_analyzer.supplier_data.get(supplier_id, {})
        if sup_data.get("unit_cost"):
            return float(sup_data["unit_cost"])
        
        return float(material.get("unit_cost", default_cost))
    
    def generate_candidates(self, suppliers: List[Dict], current_share_map: Dict,
                           delta_min: float = 0.02, delta_max: float = 0.15,
                           delta_step: float = 0.01, min_share: float = 0.10,
                           max_share: float = 0.90) -> List[Dict]:
        """
        Tedarikçi pay değişim adaylarını oluştur
        i -> j transfer: share_i -= d, share_j += d
        """
        sids = [str(s.get("supplier_id")) for s in suppliers if s.get("supplier_id")]
        cands = []
        deltas = np.arange(delta_min, delta_max + 1e-9, delta_step)
        
        for i in sids:
            for j in sids:
                if i == j:
                    continue
                si = float(current_share_map.get(i, 0.0))
                sj = float(current_share_map.get(j, 0.0))
                for d in deltas:
                    ni = si - d
                    nj = sj + d
                    if ni < min_share - 1e-9 or ni > max_share + 1e-9:
                        continue
                    if nj < min_share - 1e-9 or nj > max_share + 1e-9:
                        continue
                    
                    sm = dict(current_share_map)
                    sm[i] = ni
                    sm[j] = nj
                    
                    total = sum(sm.values())
                    if total > 0:
                        for k in sm:
                            sm[k] = sm[k] / total
                    
                    cands.append(sm)
        
        cands.insert(0, dict(current_share_map))
        return cands
    
    def calculate_weighted_supplier_factor(self, suppliers: List[Dict]) -> float:
        """Ağırlıklı tedarikçi faktörünü hesapla"""
        total_weight = 0
        weighted_factor = 0
        
        for s in suppliers:
            sid = s.get("supplier_id")
            share = s.get("share", 0)
            sup_data = self.supplier_analyzer.supplier_data.get(sid, {})
            factor = sup_data.get("supplier_factor", 1.0)
            weighted_factor += share * factor
            total_weight += share
        
        return weighted_factor / total_weight if total_weight > 0 else 1.0
    
    def calculate_weighted_risk_score(self, suppliers: List[Dict]) -> float:
        """Ağırlıklı risk skorunu hesapla"""
        total_weight = 0
        weighted_risk = 0
        
        for s in suppliers:
            sid = s.get("supplier_id")
            share = s.get("share", 0)
            risk = self.supplier_analyzer.get_supplier_risk_score(sid)
            weighted_risk += share * risk
            total_weight += share
        
        return weighted_risk / total_weight if total_weight > 0 else 0.5


# Simülasyon sonuçlarından risk hesaplama (Core'dan)
def calculate_tail_risk_from_simulation(shortage_paths: np.ndarray, service_level: float = 0.95) -> float:
    """Simülasyon sonuçlarından tail risk hesapla"""
    try:
        if shortage_paths.size == 0:
            return 0
        
        all_shortages = shortage_paths.flatten()
        positive_shortages = all_shortages[all_shortages > 0]
        
        if len(positive_shortages) < 10:
            return 0.1
        
        sorted_shortages = np.sort(positive_shortages)
        n = len(sorted_shortages)
        worst_index = int(np.ceil(0.95 * n))
        worst_index = min(worst_index, n - 1)
        worst_5_percent = sorted_shortages[worst_index:]
        
        overall_mean = np.mean(positive_shortages)
        worst_mean = np.mean(worst_5_percent) if len(worst_5_percent) > 0 else sorted_shortages[-1]
        
        if overall_mean > 0:
            tail_risk_ratio = worst_mean / overall_mean
        else:
            tail_risk_ratio = 1.0
        
        # Normalize et (0-1 arası)
        if tail_risk_ratio <= 1.0:
            return 0.0
        elif tail_risk_ratio <= 1.3:
            return 0.1
        elif tail_risk_ratio <= 1.6:
            return 0.2
        elif tail_risk_ratio <= 2.0:
            return 0.4
        elif tail_risk_ratio <= 3.0:
            return 0.6
        elif tail_risk_ratio <= 5.0:
            return 0.8
        else:
            return 1.0
    except Exception as e:
        print(f"Tail risk hesaplama hatası: {e}")
        return 0.0


def calculate_cvar_95(shortage_paths: np.ndarray) -> float:
    """CVaR95 hesapla (Conditional Value at Risk)"""
    try:
        if shortage_paths.size == 0:
            return 0.0
        
        total_shortages = np.sum(shortage_paths, axis=1) if shortage_paths.ndim > 1 else shortage_paths
        if len(total_shortages) == 0:
            return 0.0
        
        sorted_shortages = np.sort(total_shortages)
        cvar_index = int(0.95 * len(sorted_shortages))
        cvar_95 = np.mean(sorted_shortages[cvar_index:]) if cvar_index < len(sorted_shortages) else 0
        return float(cvar_95)
    except Exception as e:
        print(f"CVaR hesaplama hatası: {e}")
        return 0.0


def calculate_service_level_gap(actual_service_level: float, target_service_level: float = 0.95) -> Dict:
    """Servis seviyesi farkını hesapla"""
    gap = actual_service_level - target_service_level
    return {
        'actual': round(actual_service_level, 4),
        'target': target_service_level,
        'gap': round(gap, 4),
        'gap_percent': round(gap * 100, 2),
        'status': '✅ Yeterli' if gap >= 0 else '⚠️ Yetersiz'
    }