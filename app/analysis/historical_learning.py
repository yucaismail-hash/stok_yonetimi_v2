import json
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.learning import LearningSystem

class HistoricalLearningSystem:
    """
    Tarihsel verilerden kayan pencere yöntemiyle öğrenme sistemi
    Dokümandaki: 8 hafta eğitim, 4 hafta test
    """
    
    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = data_dir
        self.train_window = 8  # Eğitim için hafta sayısı
        self.test_window = 4   # Test için hafta sayısı
        self.learning_system = LearningSystem(data_dir)
        self.pattern_analyzer = AdvancedDemandAnalyzer()
        self.ss_optimizer = ComprehensiveSafetyStockOptimizer()
        
        # Öğrenme geçmişi
        self.learning_history = []
        self.load_history()
        
    def load_history(self):
        """Öğrenme geçmişini yükle"""
        try:
            history_file = os.path.join(self.data_dir, "learning_history.json")
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.learning_history = json.load(f)
        except Exception as e:
            print(f"Öğrenme geçmişi yüklenirken hata: {e}")
    
    def save_history(self):
        """Öğrenme geçmişini kaydet"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            history_file = os.path.join(self.data_dir, "learning_history.json")
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Öğrenme geçmişi kaydedilirken hata: {e}")
    
    def learn_from_material(self, material_code: str, group: str, 
                           weekly_data: List[float], lead_time_days: int,
                           service_level: float = 0.95) -> Dict:
        """
        Tek bir malzemenin verilerinden kayan pencere ile öğren
        """
        if len(weekly_data) < self.train_window + self.test_window:
            return {
                'success': False,
                'error': f'Yetersiz veri: En az {self.train_window + self.test_window} hafta gerekli'
            }
        
        results = {
            'success': True,
            'material_code': material_code,
            'group': group,
            'total_windows': 0,
            'successful_learning': 0,
            'windows': [],
            'seasonal_learnings': [],
            'pattern_learnings': [],
            'errors': []
        }
        
        # Kayan pencere döngüsü
        for start_idx in range(0, len(weekly_data) - self.train_window - self.test_window + 1):
            train_data = weekly_data[start_idx:start_idx + self.train_window]
            test_data = weekly_data[start_idx + self.train_window:start_idx + self.train_window + self.test_window]
            
            window_result = self._process_window(
                material_code=material_code,
                group=group,
                train_data=train_data,
                test_data=test_data,
                lead_time_days=lead_time_days,
                service_level=service_level,
                window_start=start_idx
            )
            
            results['windows'].append(window_result)
            results['total_windows'] += 1
            
            if window_result.get('success', False):
                results['successful_learning'] += 1
                
                # Mevsimsel öğrenmeyi kaydet
                if 'seasonal_learning' in window_result:
                    results['seasonal_learnings'].append(window_result['seasonal_learning'])
                
                # Pattern öğrenmeyi kaydet
                if 'pattern_learning' in window_result:
                    results['pattern_learnings'].append(window_result['pattern_learning'])
            else:
                results['errors'].append(window_result.get('error', 'Bilinmeyen hata'))
        
        # Öğrenme geçmişine ekle
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'material_code': material_code,
            'group': group,
            'total_windows': results['total_windows'],
            'successful_learning': results['successful_learning'],
            'seasonal_learnings': results['seasonal_learnings'][-10:],  # Son 10'u sakla
            'pattern_learnings': results['pattern_learnings'][-10:]
        }
        self.learning_history.append(history_entry)
        self.save_history()
        
        return results
    
    def _process_window(self, material_code: str, group: str,
                       train_data: List[float], test_data: List[float],
                       lead_time_days: int, service_level: float,
                       window_start: int) -> Dict:
        """
        Tek bir pencereyi işle
        """
        try:
            # 1. Eğitim verisinden pattern analizi
            pattern, pattern_stats = self.pattern_analyzer.analyze_demand_pattern(train_data)
            
            # 2. AI emniyet stoğu hesapla (eğitim verisi ile)
            all_methods = self.ss_optimizer.calculate_all_methods(
                train_data, lead_time_days, service_level
            )
            ai_ss = all_methods.get('hybrid_ss', 0)
            
            # 3. Gerçek ihtiyaç (test verisinden)
            actual_need = self._calculate_actual_need(test_data, lead_time_days)
            
            if ai_ss <= 0 or actual_need <= 0:
                return {
                    'success': False,
                    'error': 'Geçersiz SS değerleri'
                }
            
            # 4. Çarpan hesapla
            multiplier = actual_need / ai_ss
            multiplier = max(0.3, min(3.0, multiplier))
            
            # 5. Mevsimsel öğrenme (grup + ay + pattern)
            month = datetime.now().month
            seasonal_key = f"{group}_M{month:02d}_{pattern}"
            
            seasonal_learning = {
                'key': seasonal_key,
                'multiplier': multiplier,
                'ai_ss': ai_ss,
                'actual_need': actual_need
            }
            
            # 6. Pattern öğrenme (grup + pattern)
            pattern_key = f"{group}_{pattern}"
            pattern_learning = {
                'key': pattern_key,
                'multiplier': multiplier,
                'ai_ss': ai_ss,
                'actual_need': actual_need
            }
            
            # 7. LearningSystem'e kaydet
            self.learning_system.learn_from_material(
                material_code=material_code,
                group=group,
                pattern=pattern,
                weekly_data=train_data,
                lead_time_days=lead_time_days,
                actual_safety_stock=actual_need,
                ai_safety_stock=ai_ss
            )
            
            return {
                'success': True,
                'window_start': window_start,
                'pattern': pattern,
                'pattern_stats': pattern_stats,
                'ai_ss': ai_ss,
                'actual_need': actual_need,
                'multiplier': multiplier,
                'seasonal_learning': seasonal_learning,
                'pattern_learning': pattern_learning
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _calculate_actual_need(self, test_data: List[float], lead_time_days: int) -> float:
        """
        Test dönemindeki gerçek ihtiyacı hesapla
        Lead time boyunca oluşan maksimum talebi bul
        """
        if not test_data:
            return 0
        
        # Günlük talebe çevir (6 iş günü)
        daily_demands = []
        for week_demand in test_data:
            daily_demand = week_demand / 6
            daily_demands.extend([daily_demand] * 6)
        
        if len(daily_demands) < lead_time_days:
            return sum(daily_demands)
        
        # Lead time boyunca maksimum talep
        max_demand = 0
        for i in range(len(daily_demands) - lead_time_days + 1):
            window_sum = sum(daily_demands[i:i+lead_time_days])
            if window_sum > max_demand:
                max_demand = window_sum
        
        return max_demand
    
    def get_learning_stats(self) -> Dict:
        """
        Öğrenme istatistiklerini getir
        """
        return {
            'total_learning_entries': len(self.learning_history),
            'last_learning': self.learning_history[-1] if self.learning_history else None,
            'success_rate': self._calculate_success_rate()
        }
    
    def _calculate_success_rate(self) -> float:
        """Başarı oranını hesapla"""
        if not self.learning_history:
            return 0.0
        
        total = 0
        success = 0
        for entry in self.learning_history:
            total += entry.get('total_windows', 0)
            success += entry.get('successful_learning', 0)
        
        return success / total if total > 0 else 0.0
    
    def get_material_learning(self, material_code: str) -> Optional[Dict]:
        """
        Belirli bir malzemenin öğrenme geçmişini getir
        """
        for entry in self.learning_history:
            if entry.get('material_code') == material_code:
                return entry
        return None