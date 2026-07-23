# app/services/dashboard_summary_engine.py - GÜNCELLENMİŞ
"""
Dashboard Summary Engine - Tüm analiz sonuçlarını özetler.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import User, AnalysisResult, AnalysisDataset, UserMaterial
from app.schemas.dashboard import DashboardSummary, AlertItem

logger = logging.getLogger(__name__)


class DashboardSummaryEngine:
    """
    Dashboard Summary Engine - Tüm analiz sonuçlarını özetler.
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Tüm analiz sonuçlarını toplar ve özetler.
        """
        modules = {
            'forecast': self._get_forecast_summary,
            'safety_stock': self._get_safety_stock_summary,
            'supplier': self._get_supplier_summary,
            'simulation': self._get_simulation_summary,
            'backtest': self._get_backtest_summary,
        }
        
        result = {}
        all_summaries = []
        
        for key, func in modules.items():
            try:
                summary = func()
                if summary:
                    result[key] = summary
                    all_summaries.append(summary)
            except Exception as e:
                logger.error(f"❌ {key} özet hatası: {e}")
                result[key] = None
        
        # En yüksek priority'yi bul
        top_priority = 0
        top_module = None
        for key, data in result.items():
            if data and data.get('priority', 0) > top_priority:
                top_priority = data.get('priority', 0)
                top_module = key
        
        # Genel özet oluştur
        summary_text = self._generate_overall_summary(result, top_module)
        
        return {
            'modules': result,
            'top_priority_module': top_module,
            'top_priority': top_priority,
            'summary': summary_text,
            'updated_at': datetime.utcnow().isoformat()
        }
    
    def get_all_alerts(self) -> List[Dict[str, Any]]:
        """Tüm modüllerin attention'larını toplar. critical_items ve ai_comment ile zenginleştirir."""
        summary = self.get_dashboard_summary()
        alerts = []
        
        modules = summary.get('modules', {})
        if not modules:
            return alerts
        
        for module_key, module_data in modules.items():
            if not module_data:
                continue
            
            attention_list = module_data.get('attention', [])
            if not attention_list:
                continue
            
            priority = module_data.get('priority', 0)
            severity = self._get_severity(priority)
            page = module_data.get('target_page', '/dashboard')
            analysis_id = module_data.get('analysis_id')
            analysis_type = module_data.get('analysis_type', module_key)
            dataset_id = module_data.get('dataset_id')
            
            # ✅ critical_items'i al
            critical_items = module_data.get('critical_items', [])
            
            # ✅ AI comment'i al (varsa)
            ai_comment = module_data.get('ai_comment', '')
            
            # Eğer critical_items yoksa ve safety_stock ise, results'dan çıkar
            if not critical_items and module_key == 'safety_stock':
                # Safety Stock sonuçlarından kritikleri çıkar
                critical_items = self._get_safety_stock_critical_items(module_data)
            
            for idx, attention_text in enumerate(attention_list):
                alerts.append({
                    'id': f"{module_key}_{idx}",
                    'severity': severity,
                    'title': attention_text[:100],
                    'description': module_data.get('summary', '')[:200],
                    'action_label': 'İncele →',
                    'action_path': page,
                    'priority': priority,
                    'analysis_id': analysis_id,
                    'analysis_type': analysis_type,
                    'dataset_id': dataset_id,
                    'critical_items': critical_items[:10],  # Max 10 kritik
                    'ai_comment': ai_comment or self._generate_ai_comment(module_key, module_data)
                })
        
        alerts.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return alerts[:10]
    
    def _get_safety_stock_critical_items(self, module_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Safety Stock'dan kritik ürünleri çıkarır."""
        critical_items = module_data.get('critical_items', [])
        if critical_items:
            return critical_items
        
        # Fallback: dashboard_summary içindeki critical_items
        return module_data.get('critical_items', [])

    def _generate_ai_comment(self, module_key: str, module_data: Dict[str, Any]) -> str:
        """Modül verisine göre AI yorumu oluşturur."""
        if module_key == 'safety_stock':
            critical_count = module_data.get('critical_count', 0)
            if critical_count > 0:
                return f"{critical_count} kritik ürün tespit edildi. Stok seviyeleri hızlıca gözden geçirilmeli ve acil siparişler oluşturulmalıdır."
            return "Mevcut stok seviyeleri güvenli aralıkta."
        
        elif module_key == 'supplier':
            high_risk = module_data.get('high_risk_count', 0)
            if high_risk > 0:
                return f"{high_risk} tedarikçi yüksek risk taşıyor. Alternatif tedarikçi değerlendirilmeli."
            return "Tedarikçi riskleri kontrol altında."
        
        elif module_key == 'forecast':
            trend_up = module_data.get('trend_up', 0)
            trend_down = module_data.get('trend_down', 0)
            if trend_up > trend_down:
                return f"Talep artış trendi var. Stok seviyeleri artırılmalı."
            elif trend_down > trend_up:
                return f"Talep azalış trendi var. Stok seviyeleri gözden geçirilmeli."
            return "Talep trendi dengeli."
        
        return "Analiz sonuçları değerlendirilmeli."

    def _get_severity(self, priority: int) -> str:
        if priority >= 90:
            return 'critical'
        elif priority >= 70:
            return 'warning'
        elif priority >= 40:
            return 'info'
        return 'info'
    
    def _get_forecast_summary(self) -> Optional[Dict[str, Any]]:
        """Forecast özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_(['forecast_batch', 'forecast_batch_async']),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        
        # ✅ Önce dashboard_summary alanını kontrol et
        if 'dashboard_summary' in data:
            return data['dashboard_summary']
        
        # ⏳ FALLBACK: Eski veri için manuel
        results = data.get('results', [])
        if not results:
            return None
        
        from app.services.dashboard_summary_builder import build_forecast_dashboard_summary
        return build_forecast_dashboard_summary(
            results=results,
            analysis_id=last_result.id,
            dataset_id=last_result.upload_id
        )
    
    def _get_safety_stock_summary(self) -> Optional[Dict[str, Any]]:
        """Safety Stock özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_(['safety_stock_batch', 'safety_stock_batch_async']),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        
        if 'dashboard_summary' in data:
            return data['dashboard_summary']
        
        results = data.get('results', [])
        if not results:
            return None
        
        from app.services.dashboard_summary_builder import build_safety_stock_dashboard_summary
        return build_safety_stock_dashboard_summary(
            results=results,
            analysis_id=last_result.id,
            dataset_id=last_result.upload_id,
            service_level=data.get('service_level', 0.95)
        )
    
    def _get_supplier_summary(self) -> Optional[Dict[str, Any]]:
        """Supplier özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_(['supplier_batch', 'supplier_batch_async']),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        
        if 'dashboard_summary' in data:
            return data['dashboard_summary']
        
        suppliers = data.get('suppliers', data.get('results', []))
        if not suppliers:
            return None
        
        from app.services.dashboard_summary_builder import build_supplier_dashboard_summary
        return build_supplier_dashboard_summary(
            suppliers=suppliers,
            analysis_id=last_result.id,
            dataset_id=last_result.upload_id
        )
    
    def _get_simulation_summary(self) -> Optional[Dict[str, Any]]:
        """Simulation özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_(['simulation_batch', 'simulation_batch_async']),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        
        if 'dashboard_summary' in data:
            return data['dashboard_summary']
        
        results = data.get('results', [])
        if not results:
            return None
        
        from app.services.dashboard_summary_builder import build_simulation_dashboard_summary
        return build_simulation_dashboard_summary(
            results=results,
            analysis_id=last_result.id,
            dataset_id=last_result.upload_id,
            config=data.get('config', {})
        )
    
    def _get_backtest_summary(self) -> Optional[Dict[str, Any]]:
        """Backtest özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_(['backtest_batch', 'backtest_batch_async']),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        
        if 'dashboard_summary' in data:
            return data['dashboard_summary']
        
        results = data.get('results', [])
        if not results:
            return None
        
        from app.services.dashboard_summary_builder import build_backtest_dashboard_summary
        return build_backtest_dashboard_summary(
            results=results,
            analysis_id=last_result.id,
            dataset_id=last_result.upload_id,
            test_window=data.get('test_window', 8)
        )
    
    def _generate_overall_summary(self, modules: dict, top_module: str) -> str:
        """Genel özet oluştur."""
        if not modules:
            return "Henüz analiz yapılmamış."
        
        active_modules = [k for k, v in modules.items() if v is not None]
        if not active_modules:
            return "Henüz analiz yapılmamış."
        
        total_analyses = len(active_modules)
        high_priority = any(v.get('priority', 0) >= 70 for v in modules.values() if v)
        
        if high_priority:
            return f"{total_analyses} analiz tamamlandı. Yüksek öncelikli aksiyonlar mevcut."
        else:
            return f"{total_analyses} analiz tamamlandı. Sistem durumu stabil."


def get_dashboard_summary_engine(db: Session, user_id: int) -> DashboardSummaryEngine:
    return DashboardSummaryEngine(db, user_id)