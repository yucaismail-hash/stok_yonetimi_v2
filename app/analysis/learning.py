import json
import os
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import numpy as np

class LearningSystem:
    """Malzeme grubu bazlı mevsimsel öğrenme ve arşivleme sistemi"""
    
    def __init__(self, data_dir: str = "data/learning"):
        self.data_dir = data_dir
        self.learning_data = defaultdict(lambda: defaultdict(list))
        self.seasonal_multipliers = defaultdict(dict)
        self.pattern_multipliers = defaultdict(dict)
        self.load_data()
        
    def load_data(self):
        """Kaydedilmiş öğrenme verilerini yükle"""
        try:
            # Mevsimsel çarpanlar
            seasonal_file = os.path.join(self.data_dir, "seasonal_multipliers.json")
            if os.path.exists(seasonal_file):
                with open(seasonal_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.seasonal_multipliers = defaultdict(dict, data)
            
            # Pattern çarpanları
            pattern_file = os.path.join(self.data_dir, "pattern_multipliers.json")
            if os.path.exists(pattern_file):
                with open(pattern_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pattern_multipliers = defaultdict(dict, data)
                    
        except Exception as e:
            print(f"Öğrenme verileri yüklenirken hata: {e}")
    
    def save_data(self):
        """Öğrenme verilerini kaydet"""
        try:
            os.makedirs(self.data_dir, exist_ok=True)
            
            # Mevsimsel çarpanları kaydet
            with open(os.path.join(self.data_dir, "seasonal_multipliers.json"), 'w', encoding='utf-8') as f:
                json.dump(dict(self.seasonal_multipliers), f, indent=2, ensure_ascii=False)
            
            # Pattern çarpanlarını kaydet
            with open(os.path.join(self.data_dir, "pattern_multipliers.json"), 'w', encoding='utf-8') as f:
                json.dump(dict(self.pattern_multipliers), f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Öğrenme verileri kaydedilirken hata: {e}")
    
    def learn_from_material(self, material_code: str, group: str, pattern: str, 
                           weekly_data: List[float], lead_time_days: int, 
                           actual_safety_stock: float, ai_safety_stock: float):
        """
        Bir malzemenin verilerinden öğren
        """
        if actual_safety_stock <= 0 or ai_safety_stock <= 0:
            return
        
        # Çarpan hesapla
        multiplier = actual_safety_stock / ai_safety_stock
        multiplier = max(0.5, min(2.5, multiplier))  # Sınırla
        
        # Malzeme grubu bazlı mevsimsel çarpan
        month = datetime.now().month
        seasonal_key = f"{group}_M{month:02d}_{pattern}"
        
        if seasonal_key not in self.seasonal_multipliers:
            self.seasonal_multipliers[seasonal_key] = []
        
        self.seasonal_multipliers[seasonal_key].append(multiplier)
        
        # Pattern çarpanı
        pattern_key = f"{group}_{pattern}"
        if pattern_key not in self.pattern_multipliers:
            self.pattern_multipliers[pattern_key] = []
        
        self.pattern_multipliers[pattern_key].append(multiplier)
        
        # Veriyi sınırla (son 100 kayıt)
        if len(self.seasonal_multipliers[seasonal_key]) > 100:
            self.seasonal_multipliers[seasonal_key] = self.seasonal_multipliers[seasonal_key][-100:]
        
        if len(self.pattern_multipliers[pattern_key]) > 100:
            self.pattern_multipliers[pattern_key] = self.pattern_multipliers[pattern_key][-100:]
        
        # Kaydet
        self.save_data()
    
    def get_seasonal_multiplier(self, group: str, pattern: str, month: int = None) -> float:
        """
        Mevsimsel çarpanı getir
        """
        if month is None:
            month = datetime.now().month
        
        seasonal_key = f"{group}_M{month:02d}_{pattern}"
        
        if seasonal_key in self.seasonal_multipliers and self.seasonal_multipliers[seasonal_key]:
            # Son 10 değerin ortalaması
            values = self.seasonal_multipliers[seasonal_key][-10:]
            return np.mean(values)
        
        # Grup bazlı genel çarpan
        pattern_key = f"{group}_{pattern}"
        if pattern_key in self.pattern_multipliers and self.pattern_multipliers[pattern_key]:
            values = self.pattern_multipliers[pattern_key][-10:]
            return np.mean(values)
        
        # Varsayılan
        return 1.0
    
    def get_pattern_multiplier(self, group: str, pattern: str) -> float:
        """
        Pattern çarpanını getir
        """
        pattern_key = f"{group}_{pattern}"
        
        if pattern_key in self.pattern_multipliers and self.pattern_multipliers[pattern_key]:
            values = self.pattern_multipliers[pattern_key][-20:]
            return np.mean(values)
        
        return 1.0
    
    def get_confidence(self, group: str, pattern: str) -> float:
        """
        Öğrenme güven seviyesini getir (0-1)
        """
        pattern_key = f"{group}_{pattern}"
        if pattern_key in self.pattern_multipliers:
            count = len(self.pattern_multipliers[pattern_key])
            return min(1.0, count / 50)  # 50 kayıttan sonra maksimum güven
        return 0.1
    
    def get_learning_stats(self) -> Dict:
        """Öğrenme istatistiklerini getir"""
        total_seasonal = sum(len(v) for v in self.seasonal_multipliers.values())
        total_pattern = sum(len(v) for v in self.pattern_multipliers.values())
        
        return {
            'seasonal_keys': len(self.seasonal_multipliers),
            'pattern_keys': len(self.pattern_multipliers),
            'total_seasonal_entries': total_seasonal,
            'total_pattern_entries': total_pattern,
            'unique_groups': len(set(k.split('_')[0] for k in self.pattern_multipliers.keys()))
        }