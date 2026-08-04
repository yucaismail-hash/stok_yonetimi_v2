# app/services/ai/ai_decision_engine.py
"""
AI Decision Engine - LLM çıktısını standart karar nesnesine dönüştürür

DOCUMENT 01:
- AI does NOT replace analytical models
- AI consumes analytical outputs
- AI produces business decisions
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .provider_manager import get_provider_manager
from .prompt_builder import PromptBuilder
from .ai_exceptions import AIProviderError
from .base_provider import AIResponse

logger = logging.getLogger(__name__)


class AIDecisionEngine:
    """
    AI Decision Engine - Mevcut altyapının üzerinde çalışan karar katmanı.
    LLM çıktısını standart karar nesnesine dönüştürür.
    """
    
    def __init__(self, language: str = "Türkçe"):
        self.language = language
        self.provider_manager = get_provider_manager()
        self.prompt_builder = PromptBuilder(language=language)
    
    def generate_decision(
        self,
        analysis_type: str,
        analysis_data: Dict[str, Any],
        material_data: Optional[Dict[str, Any]] = None,
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analiz verisinden AI kararı üretir.
        
        Args:
            analysis_type: Analiz türü (safety_stock, forecast, simulation, backtest, supplier, trend, executive)
            analysis_data: Analiz sonuçları
            material_data: Malzeme bazlı veri (opsiyonel)
            provider_name: Kullanılacak provider (opsiyonel)
            
        Returns:
            {
                "decision": "increase_safety_stock",
                "priority": "high",
                "confidence": 0.93,
                "reasons": ["high_variability", "intermittent_demand"],
                "expected_impact": {...},
                "next_review_days": 30,
                "explanation": "..."
            }
        """
        try:
            # 1. Veriyi hazırla
            stats = self._extract_decision_stats(analysis_type, analysis_data, material_data)
            
            # 2. Prompt oluştur
            prompt = self._build_prompt(analysis_type, stats)
            
            # 3. Provider'dan karar al
            provider = self.provider_manager.get_provider(provider_name)
            if not provider:
                provider = self.provider_manager.get_active_provider()
            
            response: AIResponse = provider.generate(
                prompt,
                temperature=0.2,
                max_tokens=800
            )
            
            # 4. JSON parse et
            try:
                raw_decision = json.loads(response.content)
            except json.JSONDecodeError:
                logger.warning(f"JSON parse hatası, fallback kullanılıyor: {response.content[:200]}")
                return self._get_fallback_decision(analysis_type, analysis_data)
            
            # 5. Kararı standardize et
            decision = self._standardize_decision(raw_decision, analysis_type)
            
            # 6. Provider bilgisini ekle
            decision['provider'] = response.provider
            decision['model'] = response.model
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ AI Decision Engine hatası: {e}")
            return self._get_fallback_decision(analysis_type, analysis_data)
    
    def _extract_decision_stats(
        self,
        analysis_type: str,
        data: Dict[str, Any],
        material_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analiz verisinden karar istatistikleri çıkarır"""
        stats = {
            'analysis_type': analysis_type,
            'total_items': 0,
            'language': self.language,
        }
        
        # Ana veri
        results = data.get('results', [])
        if isinstance(results, dict):
            results = list(results.values()) if results else []
        
        stats['total_items'] = len(results)
        
        if analysis_type == 'safety_stock':
            stats.update(self._extract_safety_stock_stats(results))
        elif analysis_type == 'forecast':
            stats.update(self._extract_forecast_stats(results))
        elif analysis_type == 'simulation':
            stats.update(self._extract_simulation_stats(results))
        elif analysis_type == 'backtest':
            stats.update(self._extract_backtest_stats(results))
        elif analysis_type == 'supplier':
            stats.update(self._extract_supplier_stats(results))
        elif analysis_type == 'trend':
            stats.update(self._extract_trend_stats(data))
        elif analysis_type == 'executive':
            stats.update(self._extract_executive_stats(data))
        
        # Malzeme bazlı veri varsa ekle
        if material_data:
            stats['material'] = material_data
        
        return stats
    
    def _extract_safety_stock_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Safety Stock verisinden karar istatistikleri"""
        if not results:
            return {}
        
        critical_items = []
        high_risk_count = 0
        intermittent_count = 0
        seasonal_count = 0
        avg_cv = 0
        avg_risk = 0
        total_items = len(results)
        
        for r in results:
            risk = r.get('risk_score', 0)
            avg_risk += risk
            
            if risk > 0.5:
                high_risk_count += 1
                critical_items.append({
                    'code': r.get('material_code', r.get('sku', '')),
                    'risk_score': risk,
                    'cv': r.get('cv', 0),
                    'ss': r.get('recommended_value', r.get('safety_stock', 0))
                })
            
            if r.get('is_intermittent', False):
                intermittent_count += 1
            if r.get('has_seasonality', False):
                seasonal_count += 1
            avg_cv += r.get('cv', 0)
        
        avg_cv = avg_cv / total_items if total_items else 0
        avg_risk = avg_risk / total_items if total_items else 0
        
        top_risk = max(critical_items, key=lambda x: x['risk_score']) if critical_items else None
        
        return {
            'critical_count': len(critical_items),
            'high_risk_count': high_risk_count,
            'intermittent_count': intermittent_count,
            'seasonal_count': seasonal_count,
            'avg_cv': round(avg_cv, 3),
            'avg_risk': round(avg_risk, 3),
            'total_items': total_items,
            'critical_items': critical_items[:5],
            'top_risk_item': top_risk
        }
    
    def _extract_forecast_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Forecast verisinden karar istatistikleri"""
        if not results:
            return {}
        
        model_dist = {}
        trend_up = 0
        trend_down = 0
        avg_rmse = 0
        outlier_count = 0
        total_items = len(results)
        
        for r in results:
            model = r.get('selected_model', r.get('model', 'auto'))
            model_dist[model] = model_dist.get(model, 0) + 1
            
            trend = r.get('trend_direction', '')
            if trend == 'Artış' or trend == 'Increasing':
                trend_up += 1
            elif trend == 'Azalış' or trend == 'Decreasing':
                trend_down += 1
            
            rmse = r.get('model_rmse', r.get('rmse', 0))
            if rmse:
                avg_rmse += rmse
            
            if r.get('outlier_info', {}).get('has_outliers', False):
                outlier_count += 1
        
        avg_rmse = avg_rmse / total_items if total_items else 0
        
        return {
            'model_distribution': model_dist,
            'trend_up_count': trend_up,
            'trend_down_count': trend_down,
            'avg_rmse': round(avg_rmse, 2),
            'outlier_count': outlier_count,
            'total_items': total_items,
            'trend_ratio': round(trend_up / total_items if total_items else 0, 2),
        }
    
    def _extract_simulation_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Simülasyon verisinden karar istatistikleri"""
        if not results:
            return {}
        
        avg_service = 0
        avg_tail_risk = 0
        high_risk_count = 0
        low_service_count = 0
        total_items = len(results)
        
        for r in results:
            service = r.get('service_level', 0)
            avg_service += service
            
            if service < 90:
                low_service_count += 1
            
            tail_risk = r.get('tail_risk', r.get('risk', 0))
            avg_tail_risk += tail_risk
            
            if tail_risk > 0.5:
                high_risk_count += 1
        
        avg_service = avg_service / total_items if total_items else 0
        avg_tail_risk = avg_tail_risk / total_items if total_items else 0
        
        return {
            'avg_service_level': round(avg_service, 1),
            'avg_tail_risk': round(avg_tail_risk, 3),
            'high_risk_count': high_risk_count,
            'low_service_count': low_service_count,
            'total_items': total_items,
        }
    
    def _extract_backtest_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Backtest verisinden karar istatistikleri"""
        if not results:
            return {}
        
        avg_mape = 0
        best_model = {}
        worst_model = {}
        total_items = len(results)
        
        for r in results:
            mape = r.get('mape', 100)
            avg_mape += mape
            
            model = r.get('model', 'unknown')
            if not best_model or mape < best_model.get('mape', 100):
                best_model = {'model': model, 'mape': mape}
            if not worst_model or mape > worst_model.get('mape', 0):
                worst_model = {'model': model, 'mape': mape}
        
        avg_mape = avg_mape / total_items if total_items else 0
        
        return {
            'avg_mape': round(avg_mape, 2),
            'best_model': best_model,
            'worst_model': worst_model,
            'total_items': total_items,
        }
    
    def _extract_supplier_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Tedarikçi verisinden karar istatistikleri"""
        if not results:
            return {}
        
        high_risk_count = 0
        low_perf_count = 0
        avg_risk = 0
        avg_perf = 0
        total_items = len(results)
        
        for r in results:
            risk = r.get('risk_score', 0)
            avg_risk += risk
            if risk > 0.7:
                high_risk_count += 1
            
            perf = r.get('performance_score', 0)
            avg_perf += perf
            if perf < 0.3:
                low_perf_count += 1
        
        avg_risk = avg_risk / total_items if total_items else 0
        avg_perf = avg_perf / total_items if total_items else 0
        
        return {
            'high_risk_count': high_risk_count,
            'low_performance_count': low_perf_count,
            'avg_risk': round(avg_risk, 3),
            'avg_performance': round(avg_perf, 3),
            'total_items': total_items,
        }
    
    def _extract_trend_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Trend verisinden karar istatistikleri"""
        return {
            'trends': data.get('trends', []),
            'periods': data.get('periods', 0),
            'total_items': len(data.get('trends', [])),
        }
    
    def _extract_executive_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Executive verisinden karar istatistikleri"""
        return {
            'summary': data.get('summary', ''),
            'key_metrics': data.get('key_metrics', {}),
            'total_items': 1,
        }
    
    def _build_prompt(self, analysis_type: str, stats: Dict[str, Any]) -> str:
        """Prompt oluşturur - PromptBuilder'ı kullan"""
        prompt_methods = {
            'safety_stock': self.prompt_builder.build_safety_stock_prompt,
            'forecast': self.prompt_builder.build_forecast_prompt,
            'simulation': self.prompt_builder.build_simulation_prompt,
            'backtest': self.prompt_builder.build_backtest_prompt,
            'supplier': self.prompt_builder.build_supplier_prompt,
            'trend': self.prompt_builder.build_trend_prompt,
            'executive': self.prompt_builder.build_executive_prompt,
        }
        
        method = prompt_methods.get(analysis_type)
        if method:
            return method(stats)
        
        # Fallback: genel prompt
        return self.prompt_builder.build_safety_stock_prompt(stats)
    
    def _standardize_decision(self, raw_decision: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Ham kararı standardize eder"""
        
        # Zorunlu alanları kontrol et
        required_fields = ['manager_summary', 'overall_risk', 'recommended_actions', 'confidence_score']
        for field in required_fields:
            if field not in raw_decision:
                raw_decision[field] = self._get_default_value(field)
        
        # Decision tipini belirle (analiz tipine göre)
        decision_map = {
            'safety_stock': self._get_safety_stock_decision,
            'forecast': self._get_forecast_decision,
            'simulation': self._get_simulation_decision,
            'backtest': self._get_backtest_decision,
            'supplier': self._get_supplier_decision,
            'trend': self._get_trend_decision,
            'executive': self._get_executive_decision,
        }
        
        get_decision = decision_map.get(analysis_type, self._get_default_decision)
        decision = get_decision(raw_decision)
        
        # Priority'yi belirle
        priority = self._determine_priority(raw_decision, analysis_type)
        
        # Zaman damgası ekle
        return {
            'decision': decision,
            'priority': priority,
            'confidence': min(1.0, max(0.0, raw_decision.get('confidence_score', 0.5))),
            'reasons': raw_decision.get('recommended_actions', ['No specific recommendations']),
            'expected_impact': raw_decision.get('expected_impact', {}),
            'next_review_days': self._get_review_days(priority),
            'explanation': raw_decision.get('manager_summary', 'Decision generated based on analysis.'),
            'analysis_type': analysis_type,
            'generated_at': datetime.utcnow().isoformat(),
            'raw_decision': raw_decision,
        }
    
    def _get_safety_stock_decision(self, raw: Dict) -> str:
        risk = raw.get('overall_risk', 'Medium')
        if risk == 'High':
            return 'increase_safety_stock'
        elif risk == 'Low':
            return 'maintain_current'
        return 'review_safety_stock'
    
    def _get_forecast_decision(self, raw: Dict) -> str:
        return 'review_forecast_model' if raw.get('confidence_score', 0) < 0.7 else 'maintain_current'
    
    def _get_simulation_decision(self, raw: Dict) -> str:
        risk = raw.get('overall_risk', 'Medium')
        return 'urgent_action' if risk == 'High' else 'normal_monitoring'
    
    def _get_backtest_decision(self, raw: Dict) -> str:
        return 'change_forecast_model' if raw.get('confidence_score', 0) < 0.6 else 'maintain_current'
    
    def _get_supplier_decision(self, raw: Dict) -> str:
        risk = raw.get('overall_risk', 'Medium')
        return 'review_supplier' if risk == 'High' else 'maintain_current'
    
    def _get_trend_decision(self, raw: Dict) -> str:
        direction = raw.get('trend_direction', 'Stable')
        if direction == 'Deteriorating':
            return 'urgent_action'
        elif direction == 'Improving':
            return 'maintain_current'
        return 'normal_monitoring'
    
    def _get_executive_decision(self, raw: Dict) -> str:
        direction = raw.get('company_direction', 'Stable')
        if direction == 'Deteriorating':
            return 'urgent_action'
        return 'normal_monitoring'
    
    def _get_default_decision(self, raw: Dict) -> str:
        return 'maintain_current'
    
    def _determine_priority(self, raw: Dict, analysis_type: str) -> str:
        risk = raw.get('overall_risk', 'Medium')
        if risk == 'High':
            return 'critical'
        elif risk == 'Medium':
            return 'high'
        return 'medium'
    
    def _get_review_days(self, priority: str) -> int:
        return {'critical': 7, 'high': 14, 'medium': 30, 'low': 60}.get(priority, 30)
    
    def _get_default_value(self, field: str) -> Any:
        defaults = {
            'manager_summary': 'Analysis completed. Review recommendations.',
            'overall_risk': 'Medium',
            'recommended_actions': ['Monitor closely', 'Review next month'],
            'confidence_score': 0.5,
        }
        return defaults.get(field, '')
    
    def _get_fallback_decision(self, analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Hata durumunda fallback kararı"""
        return {
            'decision': 'maintain_current',
            'priority': 'medium',
            'confidence': 0.3,
            'reasons': ['AI Decision Engine could not process the data'],
            'expected_impact': {},
            'next_review_days': 14,
            'explanation': 'Karar motoru veriyi işleyemedi. Lütfen verileri kontrol edin ve tekrar deneyin.',
            'analysis_type': analysis_type,
            'generated_at': datetime.utcnow().isoformat(),
            'is_fallback': True
        }