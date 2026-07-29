# app/services/ai/ai_decision_engine.py
# AI Decision Engine - LLM çıktısını standart karar nesnesine dönüştürür

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.services.ai import get_llm_service, PromptBuilder, AIProviderError

logger = logging.getLogger(__name__)


class AIDecisionEngine:
    """
    AI Decision Engine - Mevcut Gemini altyapısının üzerinde çalışan karar katmanı.
    LLM çıktısını standart karar nesnesine dönüştürür.
    """
    
    def __init__(self, language: str = "English"):
        self.language = language
        self.llm_service = get_llm_service()
        self.prompt_builder = PromptBuilder(language=language)
    
    def generate_decision(
        self,
        analysis_type: str,
        analysis_data: Dict[str, Any],
        material_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analiz verisinden AI kararı üretir.
        
        Args:
            analysis_type: Analiz türü (safety_stock, forecast, simulation, etc.)
            analysis_data: Analiz sonuçları
            material_data: Malzeme bazlı veri (opsiyonel)
            
        Returns:
            {
                "decision": "increase_safety_stock",
                "priority": "high",
                "confidence": 0.93,
                "reasons": ["high_variability", "intermittent_demand", "summer_pattern"],
                "expected_impact": {
                    "stockout_risk": "-42%",
                    "inventory_cost": "+8%"
                },
                "next_review_days": 30,
                "explanation": "..."
            }
        """
        try:
            # 1. Veriyi hazırla
            stats = self._extract_decision_stats(analysis_type, analysis_data, material_data)
            
            # 2. Prompt oluştur
            prompt = self._build_decision_prompt(analysis_type, stats)
            
            # 3. LLM'den karar al
            result = self.llm_service.generate_json(
                prompt,
                temperature=0.2,
                max_tokens=500
            )
            
            # 4. Kararı standardize et
            decision = self._standardize_decision(result, analysis_type)
            
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
            'total_items': 0
        }
        
        # Ana veri
        results = data.get('results', [])
        stats['total_items'] = len(results)
        
        if analysis_type == 'safety_stock':
            stats.update(self._extract_safety_stock_stats(results))
        elif analysis_type == 'forecast':
            stats.update(self._extract_forecast_stats(results))
        elif analysis_type == 'simulation':
            stats.update(self._extract_simulation_stats(results))
        elif analysis_type == 'supplier':
            stats.update(self._extract_supplier_stats(results))
        
        # Malzeme bazlı veri varsa ekle
        if material_data:
            stats['material'] = material_data
        
        return stats
    
    def _extract_safety_stock_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Safety Stock verisinden karar istatistikleri"""
        if not results:
            return {}
        
        # Kritik ürünler
        critical_items = []
        high_risk_count = 0
        intermittent_count = 0
        seasonal_count = 0
        avg_cv = 0
        avg_risk = 0
        
        for r in results:
            risk = r.get('risk_score', 0)
            avg_risk += risk
            
            if risk > 0.5:
                high_risk_count += 1
                critical_items.append({
                    'code': r.get('material_code', ''),
                    'risk_score': risk,
                    'cv': r.get('cv', 0),
                    'ss': r.get('recommended_value', 0)
                })
            
            if r.get('is_intermittent'):
                intermittent_count += 1
            if r.get('has_seasonality'):
                seasonal_count += 1
            avg_cv += r.get('cv', 0)
        
        avg_cv = avg_cv / len(results) if results else 0
        avg_risk = avg_risk / len(results) if results else 0
        
        # En yüksek riskli ürün
        top_risk = max(critical_items, key=lambda x: x['risk_score']) if critical_items else None
        
        return {
            'critical_count': len(critical_items),
            'high_risk_count': high_risk_count,
            'intermittent_count': intermittent_count,
            'seasonal_count': seasonal_count,
            'avg_cv': avg_cv,
            'avg_risk': avg_risk,
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
        
        for r in results:
            model = r.get('selected_model', 'auto')
            model_dist[model] = model_dist.get(model, 0) + 1
            
            trend = r.get('trend_direction', '')
            if trend == 'Artış':
                trend_up += 1
            elif trend == 'Azalış':
                trend_down += 1
            
            rmse = r.get('model_rmse', 0)
            if rmse:
                avg_rmse += rmse
            
            if r.get('outlier_info', {}).get('has_outliers'):
                outlier_count += 1
        
        avg_rmse = avg_rmse / len(results) if results else 0
        
        return {
            'model_distribution': model_dist,
            'trend_up_count': trend_up,
            'trend_down_count': trend_down,
            'avg_rmse': avg_rmse,
            'outlier_count': outlier_count,
            'total_items': len(results)
        }
    
    def _extract_simulation_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Simülasyon verisinden karar istatistikleri"""
        if not results:
            return {}
        
        avg_service = 0
        avg_tail_risk = 0
        high_risk_count = 0
        low_service_count = 0
        
        for r in results:
            service = r.get('service_level', 0)
            avg_service += service
            
            if service < 90:
                low_service_count += 1
            
            tail_risk = r.get('tail_risk', 0)
            avg_tail_risk += tail_risk
            
            if tail_risk > 0.5:
                high_risk_count += 1
        
        avg_service = avg_service / len(results) if results else 0
        avg_tail_risk = avg_tail_risk / len(results) if results else 0
        
        return {
            'avg_service_level': avg_service,
            'avg_tail_risk': avg_tail_risk,
            'high_risk_count': high_risk_count,
            'low_service_count': low_service_count
        }
    
    def _extract_supplier_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """Tedarikçi verisinden karar istatistikleri"""
        if not results:
            return {}
        
        high_risk_count = 0
        low_perf_count = 0
        avg_risk = 0
        avg_perf = 0
        
        for r in results:
            risk = r.get('risk_score', 0)
            avg_risk += risk
            if risk > 0.7:
                high_risk_count += 1
            
            perf = r.get('performance_score', 0)
            avg_perf += perf
            if perf < 0.3:
                low_perf_count += 1
        
        avg_risk = avg_risk / len(results) if results else 0
        avg_perf = avg_perf / len(results) if results else 0
        
        return {
            'high_risk_count': high_risk_count,
            'low_performance_count': low_perf_count,
            'avg_risk': avg_risk,
            'avg_performance': avg_perf
        }
    
    def _build_decision_prompt(self, analysis_type: str, stats: Dict[str, Any]) -> str:
        """Karar prompt'u oluşturur"""
        
        prompt = f"""
You are a Senior Supply Chain Decision Engine. Based on the analysis data provided, generate a structured decision.

**Analysis Type:** {analysis_type}

**Analysis Statistics:**
{json.dumps(stats, indent=2, ensure_ascii=False)}

Based on this data, generate a decision in the following JSON format:

{{
    "decision": "string",  // One of: increase_safety_stock, decrease_safety_stock, change_forecast_model, 
                           // review_supplier, investigate_variability, seasonal_adjustment, maintain_current
    "priority": "string",  // critical, high, medium, low
    "confidence": 0.93,    // 0-1 arası
    "reasons": ["string"], // Kısa sebepler
    "expected_impact": {{
        "stockout_risk": "-42%",
        "inventory_cost": "+8%"
    }},
    "next_review_days": 30,
    "explanation": "string"  // Detaylı açıklama
}}

**Rules:**
1. If risk > 0.5 or service_level < 90 or high_risk_count > 10% → decision should be "increase_safety_stock" or "investigate_variability"
2. If avg_service > 95 and high_risk_count < 5% → decision can be "maintain_current"
3. If forecast_rmse > 30 or outlier_count > 20% → "change_forecast_model"
4. Priority should match the urgency: critical if immediate action needed, high if within a week, medium if within a month
5. Confidence should reflect data quality and sample size
6. Provide specific, actionable reasons

Return ONLY valid JSON, no other text.
"""
        return prompt
    
    def _standardize_decision(self, raw_decision: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
        """Ham kararı standardize eder"""
        
        # Zorunlu alanları kontrol et
        required_fields = ['decision', 'priority', 'confidence', 'reasons', 'explanation']
        for field in required_fields:
            if field not in raw_decision:
                raw_decision[field] = self._get_default_value(field)
        
        # Decision'ı doğrula
        valid_decisions = [
            'increase_safety_stock', 'decrease_safety_stock', 'change_forecast_model',
            'review_supplier', 'investigate_variability', 'seasonal_adjustment', 
            'maintain_current', 'urgent_action', 'normal_monitoring'
        ]
        
        if raw_decision['decision'] not in valid_decisions:
            raw_decision['decision'] = 'maintain_current'
        
        # Priority'yi doğrula
        valid_priorities = ['critical', 'high', 'medium', 'low']
        if raw_decision['priority'] not in valid_priorities:
            raw_decision['priority'] = 'medium'
        
        # Confidence'ı doğrula
        if not isinstance(raw_decision['confidence'], (int, float)):
            raw_decision['confidence'] = 0.5
        raw_decision['confidence'] = max(0, min(1, raw_decision['confidence']))
        
        # Zaman damgası ekle
        raw_decision['generated_at'] = datetime.utcnow().isoformat()
        raw_decision['analysis_type'] = analysis_type
        
        return raw_decision
    
    def _get_default_value(self, field: str) -> Any:
        """Varsayılan alan değerleri"""
        defaults = {
            'decision': 'maintain_current',
            'priority': 'medium',
            'confidence': 0.5,
            'reasons': ['Insufficient data for specific decision'],
            'expected_impact': {},
            'next_review_days': 30,
            'explanation': 'Decision generated based on available data.'
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