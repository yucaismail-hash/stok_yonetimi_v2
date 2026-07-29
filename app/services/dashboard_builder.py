# app/services/dashboard_builder.py - YENİ
# Eski dashboard_summary_builder.py ve dashboard_summary_engine.py yerine

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.models import AnalysisResult
from app.schemas.dashboard import AlertItem

logger = logging.getLogger(__name__)


class DashboardBuilder:
    """
    Dashboard Builder - Tüm analiz sonuçlarından dashboard verilerini oluşturur.
    Her analiz modülü kendi özetini üretir, bu servis sadece toplar ve formatlar.
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def build_dashboard(self) -> Dict[str, Any]:
        """
        Tüm modüllerin özetlerini toplar ve dashboard verisini oluşturur.
        """
        try:
            # Son 10 analiz sonucunu al
            results = self.db.query(AnalysisResult).filter(
                AnalysisResult.user_id == self.user_id,
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).limit(10).all()
            
            modules = {}
            alerts = []
            
            for result in results:
                data = result.data or {}
                
                # AI Decision'dan özet oluştur
                ai_decision = data.get('ai_decision')
                dashboard_summary = data.get('dashboard_summary', {})
                
                if not dashboard_summary and ai_decision:
                    # AI Decision varsa ondan özet oluştur
                    dashboard_summary = self._build_summary_from_decision(
                        result.result_type,
                        result.id,
                        ai_decision,
                        data
                    )
                    # Özeti veriye kaydet (cache)
                    data['dashboard_summary'] = dashboard_summary
                    result.data = data
                    self.db.commit()
                
                if dashboard_summary:
                    module_type = result.result_type.split('_')[0]
                    modules[module_type] = dashboard_summary
                    
                    # Alert'leri topla
                    attention = dashboard_summary.get('attention', [])
                    priority = dashboard_summary.get('priority', 0)
                    for att in attention:
                        severity = 'critical' if priority > 70 else 'warning' if priority > 40 else 'info'
                        alerts.append(AlertItem(
                            id=f"{result.id}_{hash(att)}",
                            severity=severity,
                            title=att[:50],
                            description=att,
                            action_label='İncele →',
                            action_path=f'/{module_type}',
                            priority=priority,
                            analysis_id=result.id,
                            analysis_type=result.result_type,
                            dataset_id=dashboard_summary.get('dataset_id')
                        ))
            
            # Priority'ye göre sırala
            alerts.sort(key=lambda x: x.priority, reverse=True)
            
            total_priority = max([m.get('priority', 0) for m in modules.values()]) if modules else 0
            top_module = max(modules.items(), key=lambda x: x[1].get('priority', 0))[0] if modules else None
            
            return {
                'modules': modules,
                'top_priority_module': top_module,
                'top_priority': total_priority,
                'summary': self._generate_summary(modules),
                'alerts': [alert.dict() for alert in alerts[:10]],
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Dashboard builder hatası: {e}")
            return {
                'modules': {},
                'top_priority_module': None,
                'top_priority': 0,
                'summary': 'Özet oluşturulamadı.',
                'alerts': [],
                'updated_at': datetime.utcnow().isoformat()
            }
    
    def _build_summary_from_decision(
        self,
        result_type: str,
        analysis_id: int,
        ai_decision: Dict[str, Any],
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI Decision'dan dashboard summary oluşturur.
        """
        results = data.get('results', [])
        total = len(results)
        
        priority = 0
        if ai_decision.get('priority') == 'critical':
            priority = 90
        elif ai_decision.get('priority') == 'high':
            priority = 70
        elif ai_decision.get('priority') == 'medium':
            priority = 40
        else:
            priority = 20
        
        # Decision'a göre özet metni
        decision_map = {
            'increase_safety_stock': 'Emniyet stoğu artırılmalı',
            'decrease_safety_stock': 'Emniyet stoğu azaltılabilir',
            'change_forecast_model': 'Tahmin modeli değiştirilmeli',
            'review_supplier': 'Tedarikçi gözden geçirilmeli',
            'investigate_variability': 'Talep değişkenliği araştırılmalı',
            'seasonal_adjustment': 'Mevsimsel ayarlama yapılmalı',
            'maintain_current': 'Mevcut politika yeterli',
            'urgent_action': 'Acil aksiyon gerekiyor',
            'normal_monitoring': 'Normal takip yeterli'
        }
        
        decision_text = decision_map.get(ai_decision.get('decision', ''), 'Analiz tamamlandı')
        
        summary = f"{total} ürün analiz edildi. {decision_text}."
        
        return {
            'priority': priority,
            'summary': summary,
            'attention': ai_decision.get('reasons', [])[:3],
            'business_value': ai_decision.get('expected_impact', {}).get('stockout_risk', 'Beklenen fayda: Stok riski azaltılabilir.'),
            'analysis_id': analysis_id,
            'dataset_id': data.get('dataset_id'),
            'target_page': f'/{result_type.split("_")[0]}',
            'analysis_type': result_type,
            'last_run': datetime.utcnow().isoformat(),
            'status': 'success',
            'metrics': {
                'total_products': total,
                'confidence': ai_decision.get('confidence', 0.5)
            },
            'critical_items': [
                {'code': r.get('material_code', '')} 
                for r in results[:5] if r.get('risk_score', 0) > 0.5
            ],
            'high_risk_count': len([r for r in results if r.get('risk_score', 0) > 0.5]),
            'critical_count': len([r for r in results if r.get('risk_score', 0) > 0.7]),
            'trend_up': 0,
            'trend_down': 0,
            'avg_service_level': 0
        }
    
    def _generate_summary(self, modules: Dict[str, Any]) -> str:
        """Modüllerden genel özet oluşturur."""
        if not modules:
            return 'Henüz analiz yapılmadı.'
        
        parts = []
        for name, data in modules.items():
            if data:
                parts.append(f"{name}: {data.get('summary', '')}")
        
        return ' | '.join(parts) if parts else 'Analizler tamamlandı.'


def get_dashboard_builder(db: Session, user_id: int) -> DashboardBuilder:
    """DashboardBuilder instance oluşturur."""
    return DashboardBuilder(db, user_id)