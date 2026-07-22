# app/services/dashboard_summary_engine.py
"""
Dashboard Summary Engine - Tüm analiz sonuçlarını özetler.
Her modül kendi priority'sini hesaplar.
Dashboard sadece özetleri toplar ve karşılaştırır.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models import User, AnalysisResult, AnalysisDataset, UserMaterial

logger = logging.getLogger(__name__)


class DashboardSummaryEngine:
    """
    Dashboard Summary Engine - Tüm analiz sonuçlarını özetler.
    
    Görevleri:
    1. Her modülün son başarılı analizini getir
    2. Her modülden business summary çıkar
    3. Her modülün priority skorunu al
    4. Tek bir dashboard modeli oluştur
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Tüm analiz sonuçlarını toplar ve özetler.
        
        Returns:
            {
                "modules": {
                    "forecast": {...},
                    "safety_stock": {...},
                    ...
                },
                "top_priority_module": "forecast",
                "top_priority": 95,
                "summary": "Genel özet",
                "updated_at": "2026-07-22T11:34:55"
            }
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
    
    def _get_forecast_summary(self) -> Optional[Dict[str, Any]]:
        """Forecast özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.like('forecast_batch%'),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        results = data.get('results', [])
        
        # Priority hesapla
        priority = self._calculate_forecast_priority(last_result, results)
        
        # Summary oluştur
        total_items = len(results)
        if total_items == 0:
            return None
        
        # Trend analizi
        trend_up = sum(1 for r in results if r.get('trend_direction') == 'Artış')
        trend_down = sum(1 for r in results if r.get('trend_direction') == 'Azalış')
        
        if trend_up > trend_down:
            trend_text = f"{trend_up} üründe artış bekleniyor"
        else:
            trend_text = f"{trend_down} üründe azalış bekleniyor"
        
        return {
            'priority': priority,
            'summary': f"Talep {trend_text}. {total_items} ürün analiz edildi.",
            'analysis_id': last_result.id,
            'page': '/forecast',
            'analysis_type': 'forecast',
            'dataset_id': last_result.upload_id,
            'total_items': total_items,
            'trend_up': trend_up,
            'trend_down': trend_down,
            'created_at': last_result.created_at.isoformat()
        }
    
    def _get_safety_stock_summary(self) -> Optional[Dict[str, Any]]:
        """Safety Stock özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.like('safety_stock_batch%'),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        results = data.get('results', [])
        
        # Priority hesapla
        priority = self._calculate_safety_stock_priority(last_result, results)
        
        # Kritik ürünleri bul
        critical = []
        for r in results:
            if r.get('risk_level') == 'Yüksek':
                critical.append({
                    'code': r.get('material_code', ''),
                    'risk': r.get('risk_score', 0),
                    'ss': r.get('hybrid_ss', 0)
                })
        
        # Summary oluştur
        if critical:
            top_critical = critical[0]
            summary = f"{len(critical)} kritik ürün. En riskli: {top_critical.get('code', 'Bilinmiyor')}"
        else:
            summary = f"{len(results)} ürün analiz edildi, kritik ürün yok."
        
        return {
            'priority': priority,
            'summary': summary,
            'analysis_id': last_result.id,
            'page': '/safety-stock',
            'analysis_type': 'safety_stock',
            'dataset_id': last_result.upload_id,
            'total_items': len(results),
            'critical_count': len(critical),
            'critical_items': critical[:5],
            'created_at': last_result.created_at.isoformat()
        }
    
    def _get_supplier_summary(self) -> Optional[Dict[str, Any]]:
        """Supplier özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.like('supplier_batch%'),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        suppliers = data.get('suppliers', [])
        
        # Priority hesapla
        priority = self._calculate_supplier_priority(last_result, suppliers)
        
        # Riskli tedarikçileri bul
        high_risk = []
        for s in suppliers:
            if s.get('risk_level') == 'YÜKSEK':
                high_risk.append(s.get('name', 'Bilinmiyor'))
        
        # Summary oluştur
        if high_risk:
            summary = f"{len(high_risk)} tedarikçi yüksek riskli. İlk: {high_risk[0]}"
        else:
            summary = f"{len(suppliers)} tedarikçi analiz edildi."
        
        return {
            'priority': priority,
            'summary': summary,
            'analysis_id': last_result.id,
            'page': '/supplier',
            'analysis_type': 'supplier',
            'dataset_id': last_result.upload_id,
            'total_items': len(suppliers),
            'high_risk_count': len(high_risk),
            'high_risk_suppliers': high_risk[:5],
            'created_at': last_result.created_at.isoformat()
        }
    
    def _get_simulation_summary(self) -> Optional[Dict[str, Any]]:
        """Simulation özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.like('simulation_batch%'),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        results = data.get('results', [])
        
        # Priority hesapla
        priority = self._calculate_simulation_priority(last_result, results)
        
        # Ortalama servis seviyesi
        avg_service = 0
        if results:
            avg_service = sum(r.get('service_level', 0) for r in results) / len(results)
        
        # Potansiyel tasarruf
        saving_potential = 0
        if results:
            high_risk_products = [r for r in results if r.get('tail_risk', 0) > 0.4]
            if high_risk_products:
                saving_potential = len(high_risk_products) * 2
        
        return {
            'priority': priority,
            'summary': f"Ortalama servis: %{avg_service:.1f}. {len(results)} ürün simüle edildi.",
            'analysis_id': last_result.id,
            'page': '/simulation',
            'analysis_type': 'simulation',
            'dataset_id': last_result.upload_id,
            'total_items': len(results),
            'avg_service_level': round(avg_service, 1),
            'saving_potential': saving_potential,
            'created_at': last_result.created_at.isoformat()
        }
    
    def _get_backtest_summary(self) -> Optional[Dict[str, Any]]:
        """Backtest özetini çıkar."""
        last_result = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.like('backtest_batch%'),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).first()
        
        if not last_result:
            return None
        
        data = last_result.data or {}
        results = data.get('results', [])
        
        # Priority hesapla
        priority = self._calculate_backtest_priority(last_result, results)
        
        # Ortalama servis seviyesi
        avg_service = 0
        if results:
            avg_service = sum(r.get('service_level', 0) for r in results) / len(results)
        
        return {
            'priority': priority,
            'summary': f"Ortalama servis: %{avg_service:.1f}. {len(results)} ürün test edildi.",
            'analysis_id': last_result.id,
            'page': '/backtest',
            'analysis_type': 'backtest',
            'dataset_id': last_result.upload_id,
            'total_items': len(results),
            'avg_service_level': round(avg_service, 1),
            'created_at': last_result.created_at.isoformat()
        }
    
    # ============================================================
    # 📌 PRIORITY HESAPLAMA FONKSİYONLARI
    # ============================================================
    
    def _calculate_forecast_priority(self, result: AnalysisResult, results: list) -> int:
        """Forecast priority hesapla."""
        priority = 40  # Base
        
        # 1. Analiz yaşı
        days_ago = (datetime.utcnow() - result.created_at).days
        if days_ago > 30:
            priority += 30
        elif days_ago > 14:
            priority += 15
        
        # 2. Trend değişimi
        if results:
            trend_up = sum(1 for r in results if r.get('trend_direction') == 'Artış')
            trend_down = sum(1 for r in results if r.get('trend_direction') == 'Azalış')
            if trend_up > 0 and trend_down > 0:
                priority += 10
            elif abs(trend_up - trend_down) > len(results) * 0.6:
                priority += 15
        
        # 3. Outlier varlığı
        for r in results:
            if r.get('outlier_info', {}).get('has_outliers', False):
                priority += 10
                break
        
        return min(100, priority)
    
    def _calculate_safety_stock_priority(self, result: AnalysisResult, results: list) -> int:
        """Safety Stock priority hesapla."""
        priority = 40
        
        # 1. Kritik ürün sayısı
        critical = [r for r in results if r.get('risk_level') == 'Yüksek']
        critical_count = len(critical)
        
        if critical_count > 20:
            priority += 50
        elif critical_count > 10:
            priority += 35
        elif critical_count > 5:
            priority += 20
        elif critical_count > 0:
            priority += 10
        
        # 2. Sıfır talep oranı
        zero_demand = [r for r in results if r.get('zero_ratio', 0) > 0.5]
        if zero_demand:
            priority += min(15, len(zero_demand) * 2)
        
        return min(100, priority)
    
    def _calculate_supplier_priority(self, result: AnalysisResult, suppliers: list) -> int:
        """Supplier priority hesapla."""
        priority = 40
        
        # 1. Yüksek riskli tedarikçi sayısı
        high_risk = [s for s in suppliers if s.get('risk_level') == 'YÜKSEK']
        if len(high_risk) > 5:
            priority += 45
        elif len(high_risk) > 3:
            priority += 30
        elif len(high_risk) > 0:
            priority += 15
        
        # 2. Düşük performans
        low_perf = [s for s in suppliers if s.get('performance_level') == 'KÖTÜ']
        if low_perf:
            priority += min(15, len(low_perf) * 3)
        
        return min(100, priority)
    
    def _calculate_simulation_priority(self, result: AnalysisResult, results: list) -> int:
        """Simulation priority hesapla."""
        priority = 30
        
        # 1. Analiz yaşı
        days_ago = (datetime.utcnow() - result.created_at).days
        if days_ago > 60:
            priority += 25
        elif days_ago > 30:
            priority += 15
        
        # 2. Yüksek tail risk
        if results:
            high_risk = [r for r in results if r.get('tail_risk', 0) > 0.5]
            if high_risk:
                priority += min(20, len(high_risk) * 2)
        
        return min(100, priority)
    
    def _calculate_backtest_priority(self, result: AnalysisResult, results: list) -> int:
        """Backtest priority hesapla."""
        priority = 20
        
        # 1. Analiz yaşı
        days_ago = (datetime.utcnow() - result.created_at).days
        if days_ago > 90:
            priority += 20
        elif days_ago > 45:
            priority += 10
        
        # 2. Düşük servis seviyesi
        if results:
            low_service = [r for r in results if r.get('service_level', 0) < 0.85]
            if low_service:
                priority += min(15, len(low_service) * 2)
        
        return min(100, priority)
    
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
    """DashboardSummaryEngine instance'ı oluşturur."""
    return DashboardSummaryEngine(db, user_id)