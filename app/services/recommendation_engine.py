# app/services/recommendation_engine.py - GÜNCELLENMİŞ

"""
Recommendation Engine - En yüksek öncelikli aksiyonu seçer.
AI karar vermez, sadece seçilen aksiyonu açıklar.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Recommendation Engine - En yüksek öncelikli aksiyonu seçer.
    """
    
    def __init__(self, db, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def get_top_recommendation(self, dashboard_summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Dashboard summary'dan en yüksek priority'li modülü seçer.
        """
        modules = dashboard_summary.get('modules', {})
        
        active_modules = []
        for key, data in modules.items():
            if data and data.get('priority', 0) > 0:
                active_modules.append({
                    'key': key,
                    'data': data,
                    'priority': data.get('priority', 0)
                })
        
        if not active_modules:
            return None
        
        top = max(active_modules, key=lambda x: x['priority'])
        
        # ✅ target_page'yi doğru al
        target_page = top['data'].get('page', f"/{top['key']}")
        analysis_id = top['data'].get('analysis_id')
        analysis_type = top['data'].get('analysis_type', top['key'])
        dataset_id = top['data'].get('dataset_id')
        
        # ✅ Summary'yi al
        summary = top['data'].get('summary', 'Analiz sonuçları mevcut.')
        
        # ✅ Priority label'ı al
        priority = top['priority']
        priority_label = self._get_priority_label(priority)
        
        return {
            'analysis': top['key'],
            'priority': priority,
            'priority_label': priority_label,
            'title': self._generate_title(top['key'], top['data']),
            'reason': summary,
            'expected_benefit': self._generate_expected_benefit(top['key'], top['data']),
            'target_page': target_page,
            'analysis_id': analysis_id,
            'analysis_type': analysis_type,
            'dataset_id': dataset_id,
        }
    
    def _get_priority_label(self, priority: int) -> str:
        """Priority'ye göre etiket döndürür."""
        if priority >= 90:
            return 'Kritik'
        elif priority >= 70:
            return 'Yüksek'
        elif priority >= 40:
            return 'Orta'
        return 'Düşük'
    
    def _generate_title(self, module: str, data: Dict[str, Any]) -> str:
        """Modül için başlık oluşturur."""
        titles = {
            'forecast': 'Talep Tahminini Güncelle',
            'safety_stock': 'Emniyet Stoğu Analizini İncele',
            'supplier': 'Tedarikçi Riskini Değerlendir',
            'simulation': 'Simülasyon Sonuçlarını Değerlendir',
            'backtest': 'Backtest Sonuçlarını İncele',
        }
        return titles.get(module, 'Analizi İncele')
    
    def _generate_expected_benefit(self, module: str, data: Dict[str, Any]) -> str:
        """Beklenen fayda metnini oluşturur."""
        benefits = {
            'forecast': 'Güncel talep verileri ile stok planlaması optimize edilecek.',
            'safety_stock': 'Kritik ürünlerin stok seviyeleri hızlıca gözden geçirilecek.',
            'supplier': 'Tedarik zinciri riskleri değerlendirilip aksiyon alınacak.',
            'simulation': 'Farklı senaryolar ile stok performansı test edilecek.',
            'backtest': 'Geçmiş veriler ile strateji performansı doğrulanacak.',
        }
        return benefits.get(module, 'Analiz sonuçları doğrultusunda aksiyon alınacak.')