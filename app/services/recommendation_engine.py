# app/services/recommendation_engine.py
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
        
        title = self._generate_title(top['key'], top['data'])
        reason = self._generate_reason(top['key'], top['data'])
        expected_benefit = self._generate_expected_benefit(top['key'], top['data'])
        
        return {
            'analysis': top['key'],
            'priority': top['priority'],
            'title': title,
            'reason': reason,
            'expected_benefit': expected_benefit,
            'target_page': top['data'].get('page', '/dashboard'),
            'analysis_id': top['data'].get('analysis_id'),
            'analysis_type': top['data'].get('analysis_type', top['key']),
            'dataset_id': top['data'].get('dataset_id'),
        }
    
    def _generate_title(self, module: str, data: Dict[str, Any]) -> str:
        titles = {
            'forecast': 'Talep Tahminini Güncelle',
            'safety_stock': 'Emniyet Stoğu Analizini İncele',
            'supplier': 'Tedarikçi Riskini Değerlendir',
            'simulation': 'Simülasyon Sonuçlarını Değerlendir',
            'backtest': 'Backtest Sonuçlarını İncele',
        }
        return titles.get(module, 'Analizi İncele')
    
    def _generate_reason(self, module: str, data: Dict[str, Any]) -> str:
        reasons = {
            'forecast': f"Son analiz {data.get('created_at', '')} tarihinde yapıldı.",
            'safety_stock': f"{data.get('critical_count', 0)} kritik ürün tespit edildi.",
            'supplier': f"{data.get('high_risk_count', 0)} tedarikçi yüksek riskli.",
            'simulation': f"{data.get('total_items', 0)} ürün simüle edildi.",
            'backtest': f"{data.get('total_items', 0)} ürün test edildi.",
        }
        return reasons.get(module, 'Analiz sonuçları değerlendirilmeli.')
    
    def _generate_expected_benefit(self, module: str, data: Dict[str, Any]) -> str:
        benefits = {
            'forecast': 'Güncel talep verileri ile stok planlaması optimize edilecek.',
            'safety_stock': 'Kritik ürünlerin stok seviyeleri hızlıca gözden geçirilecek.',
            'supplier': 'Tedarik zinciri riskleri değerlendirilip aksiyon alınacak.',
            'simulation': 'Farklı senaryolar ile stok performansı test edilecek.',
            'backtest': 'Geçmiş veriler ile strateji performansı doğrulanacak.',
        }
        return benefits.get(module, 'Analiz sonuçları doğrultusunda aksiyon alınacak.')