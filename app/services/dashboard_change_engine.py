# app/services/dashboard_change_engine.py - DÜZELTİLMİŞ

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import AnalysisResult, User

logger = logging.getLogger(__name__)


class DashboardChangeEngine:
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def get_all_changes(self) -> Dict[str, Any]:
        """Tüm modüllerin değişimlerini hesaplar."""
        modules = {
            'forecast': self._get_forecast_changes,
            'safety_stock': self._get_safety_stock_changes,
            'supplier': self._get_supplier_changes,
            'simulation': self._get_simulation_changes,
            'backtest': self._get_backtest_changes,
        }
        
        result = {}
        for key, func in modules.items():
            try:
                changes = func()
                if changes and len(changes) > 0:
                    result[key] = changes
            except Exception as e:
                logger.error(f"❌ {key} değişim hatası: {e}")
                result[key] = None
        
        # ✅ Hiç değişim yoksa bile boş değil, has_changes false dönecek
        return result
    
    def get_gains(self) -> List[str]:
        """Değişimlerden işletme kazanımları üretir."""
        gains = []
        changes = self.get_all_changes()
        
        if not changes:
            return gains
        
        for module_key, module_changes in changes.items():
            if not module_changes:
                continue
            
            for key, value in module_changes.items():
                if key == '_meta' or not isinstance(value, dict):
                    continue
                
                change = value.get('change', 0)
                label = value.get('label', key)
                improved = value.get('improved', False)
                
                if change < 0 and improved:
                    gains.append(f"✔ {abs(change)} {label} iyileşti.")
                elif change > 0 and not improved:
                    gains.append(f"⚠ {abs(change)} {label} kötüleşti.")
                elif change > 0 and improved:
                    gains.append(f"✔ {abs(change)} {label} arttı.")
                elif change < 0 and not improved:
                    gains.append(f"⚠ {abs(change)} {label} azaldı.")
        
        return gains[:5]
    
    def _get_last_two_results(self, result_type: str) -> tuple:
        """Bir modülün son 2 başarılı analizini getirir."""
        results = self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == self.user_id,
            AnalysisResult.result_type.in_([result_type, f"{result_type}_async"]),
            AnalysisResult.status.in_(['completed', None])
        ).order_by(
            AnalysisResult.created_at.desc()
        ).limit(2).all()
        
        if len(results) < 2:
            return None, results[0] if results else None
        
        return results[1], results[0]
    
    def _get_dashboard_summary(self, result: AnalysisResult) -> Optional[Dict[str, Any]]:
        if not result:
            return None
        data = result.data or {}
        return data.get('dashboard_summary')
    
    def _get_forecast_changes(self) -> Optional[Dict[str, Any]]:
        old_result, new_result = self._get_last_two_results('forecast_batch')
        if not new_result:
            return None
        
        old_summary = self._get_dashboard_summary(old_result)
        new_summary = self._get_dashboard_summary(new_result)
        
        changes = {}
        
        if old_summary and new_summary:
            old_rmse = old_summary.get('metrics', {}).get('avg_rmse', 0)
            new_rmse = new_summary.get('metrics', {}).get('avg_rmse', 0)
            if old_rmse and new_rmse:
                rmse_change = round(new_rmse - old_rmse, 1)
                changes['accuracy'] = {
                    'old': old_rmse,
                    'new': new_rmse,
                    'change': -rmse_change,
                    'improved': rmse_change < 0,
                    'label': 'RMSE'
                }
        
        if old_summary and new_summary:
            old_up = old_summary.get('trend_up', 0)
            new_up = new_summary.get('trend_up', 0)
            if old_up or new_up:
                changes['trend_up'] = {
                    'old': old_up,
                    'new': new_up,
                    'change': new_up - old_up,
                    'improved': new_up < old_up,
                    'label': 'Artış Trendi'
                }
        
        changes['_meta'] = {
            'analysis_id': new_result.id,
            'created_at': new_result.created_at.isoformat()
        }
        
        return changes if len(changes) > 1 else None
    
    def _get_safety_stock_changes(self) -> Optional[Dict[str, Any]]:
        old_result, new_result = self._get_last_two_results('safety_stock_batch')
        if not new_result:
            return None
        
        old_summary = self._get_dashboard_summary(old_result)
        new_summary = self._get_dashboard_summary(new_result)
        
        changes = {}
        
        if old_summary and new_summary:
            old_critical = old_summary.get('critical_count', 0)
            new_critical = new_summary.get('critical_count', 0)
            if old_critical or new_critical:
                critical_change = new_critical - old_critical
                changes['critical_count'] = {
                    'old': old_critical,
                    'new': new_critical,
                    'change': critical_change,
                    'improved': critical_change < 0,
                    'label': 'Kritik Ürün'
                }
        
        changes['_meta'] = {
            'analysis_id': new_result.id,
            'created_at': new_result.created_at.isoformat()
        }
        
        return changes if len(changes) > 1 else None
    
    def _get_supplier_changes(self) -> Optional[Dict[str, Any]]:
        old_result, new_result = self._get_last_two_results('supplier_batch')
        if not new_result:
            return None
        
        old_summary = self._get_dashboard_summary(old_result)
        new_summary = self._get_dashboard_summary(new_result)
        
        changes = {}
        
        if old_summary and new_summary:
            old_risk = old_summary.get('high_risk_count', 0)
            new_risk = new_summary.get('high_risk_count', 0)
            if old_risk or new_risk:
                risk_change = new_risk - old_risk
                changes['high_risk_count'] = {
                    'old': old_risk,
                    'new': new_risk,
                    'change': risk_change,
                    'improved': risk_change < 0,
                    'label': 'Riskli Tedarikçi'
                }
        
        changes['_meta'] = {
            'analysis_id': new_result.id,
            'created_at': new_result.created_at.isoformat()
        }
        
        return changes if len(changes) > 1 else None
    
    def _get_simulation_changes(self) -> Optional[Dict[str, Any]]:
        old_result, new_result = self._get_last_two_results('simulation_batch')
        if not new_result:
            return None
        
        old_summary = self._get_dashboard_summary(old_result)
        new_summary = self._get_dashboard_summary(new_result)
        
        changes = {}
        
        if old_summary and new_summary:
            old_service = old_summary.get('avg_service_level', 0)
            new_service = new_summary.get('avg_service_level', 0)
            if old_service or new_service:
                service_change = round(new_service - old_service, 1)
                changes['avg_service_level'] = {
                    'old': old_service,
                    'new': new_service,
                    'change': service_change,
                    'improved': service_change > 0,
                    'label': 'Servis Seviyesi'
                }
        
        changes['_meta'] = {
            'analysis_id': new_result.id,
            'created_at': new_result.created_at.isoformat()
        }
        
        return changes if len(changes) > 1 else None
    
    def _get_backtest_changes(self) -> Optional[Dict[str, Any]]:
        old_result, new_result = self._get_last_two_results('backtest_batch')
        if not new_result:
            return None
        
        old_summary = self._get_dashboard_summary(old_result)
        new_summary = self._get_dashboard_summary(new_result)
        
        changes = {}
        
        if old_summary and new_summary:
            old_service = old_summary.get('avg_service_level', 0)
            new_service = new_summary.get('avg_service_level', 0)
            if old_service or new_service:
                service_change = round(new_service - old_service, 1)
                changes['avg_service_level'] = {
                    'old': old_service,
                    'new': new_service,
                    'change': service_change,
                    'improved': service_change > 0,
                    'label': 'Backtest Doğruluğu'
                }
        
        changes['_meta'] = {
            'analysis_id': new_result.id,
            'created_at': new_result.created_at.isoformat()
        }
        
        return changes if len(changes) > 1 else None


def get_dashboard_change_engine(db: Session, user_id: int) -> DashboardChangeEngine:
    return DashboardChangeEngine(db, user_id)