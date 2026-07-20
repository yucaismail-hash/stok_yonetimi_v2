# app/analysis/executive_summary_engine.py - YENİ DOSYA

"""
Executive Summary Engine - Trend + Önceki Executive
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country

logger = logging.getLogger(__name__)


class ExecutiveSummaryEngine:
    """
    Executive Summary - Trend Summary + Önceki Executive
    """
    
    def __init__(self, language: str = "English"):
        self.language = language
        self.ai_engine = AISummaryEngine(language=language)
        self.llm_service = self.ai_engine.llm_service  # ✅ DOĞRU
    
    def build_executive_summary(
        self,
        trend_summary: Dict[str, Any],
        previous_executive: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Trend summary ve önceki executive'ten yönetici özeti oluşturur
        """
        # Eğer önceki executive yoksa, trend summary'den oluştur
        if not previous_executive:
            return self._create_from_trend(trend_summary)
        
        # Trend değişmemişse, önceki executive'i döndür
        if self._is_trend_unchanged(trend_summary, previous_executive):
            return previous_executive
        
        # Yeni executive oluştur
        return self._create_executive(trend_summary, previous_executive)
    
    def _is_trend_unchanged(self, trend: Dict, previous: Dict) -> bool:
        """Trend değişmemiş mi kontrol et"""
        if not previous:
            return False
        
        prev_trend = previous.get("trend_direction")
        current_trend = trend.get("trend_direction")
        prev_risk = previous.get("risk_trend")
        current_risk = trend.get("risk_trend")
        
        return prev_trend == current_trend and prev_risk == current_risk
    
    def _create_from_trend(self, trend: Dict) -> Dict[str, Any]:
        """Sadece trend'den executive oluştur"""
        return {
            "summary": trend.get("summary", ""),
            "trend_direction": trend.get("trend_direction", "Bilinmiyor"),
            "risk_trend": trend.get("risk_trend", "Bilinmiyor"),
            "key_insights": trend.get("key_insights", []),
            "recurring_issues": trend.get("recurring_issues", []),
            "improvements": trend.get("improvements", []),
            "executive_recommendations": trend.get("executive_recommendations", []),
            "company_direction": "Bilinmiyor",
            "critical_attention": [],
            "confidence": trend.get("confidence", 0.5),
            "_meta": {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "trend_only"
            }
        }
    
    def _create_executive(self, trend: Dict, previous: Dict) -> Dict[str, Any]:
        """Executive oluştur"""
        prompt = self._build_executive_prompt(trend, previous)
        
        try:
            response = self.llm_service.generate_json(
                prompt,
                temperature=0.2,
                max_tokens=600
            )
            result = self._parse_executive_response(response)
            
            result["_meta"] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "trend_plus_previous",
                "trend_id": trend.get("_meta", {}).get("created_at"),
                "previous_id": previous.get("_meta", {}).get("created_at")
            }
            return result 
            
        except Exception as e:
            logger.error(f"Executive summary oluşturma hatası: {e}")
            return previous or self._create_from_trend(trend)
    
    def _build_executive_prompt(self, trend: Dict, previous: Dict) -> str:
        """Executive prompt oluşturur"""
        language_instructions = {
            "Türkçe": "Lütfen tüm yanıtlarını TÜRKÇE olarak ver.",
            "English": "Please respond in ENGLISH.",
        }
        lang_instruction = language_instructions.get(self.language, language_instructions["English"])
        
        return f"""
{lang_instruction}

You are a senior Supply Chain Consultant preparing an Executive Summary.

**Current Trend Summary:**
{json.dumps(trend, indent=2, ensure_ascii=False)}

**Previous Executive Summary:**
{json.dumps(previous, indent=2, ensure_ascii=False)}

**Your Task:**
Answer these questions:
1. Where is the company heading? (improving/stable/deteriorating)
2. Are risks increasing or decreasing?
3. What are the most important developments?
4. What recurring problems persist?
5. What should management focus on?

**Response Format (JSON):**
{{
  "summary": "Executive summary (2-3 sentences)",
  "company_direction": "İyileşiyor|Stabil|Kötüleşiyor",
  "risk_trend": "Azalıyor|Stabil|Artıyor",
  "key_developments": ["development1", "development2", ...],
  "recurring_problems": ["problem1", "problem2", ...],
  "critical_attention": ["attention1", "attention2", ...],
  "executive_recommendations": ["rec1", "rec2", ...],
  "confidence": 0.95
}}

IMPORTANT: Return ONLY valid JSON.
"""
    
    # app/analysis/executive_summary_engine.py - _parse_executive_response metodunu güncelle

    def _parse_executive_response(self, response: str) -> Dict[str, Any]:
        """Executive yanıtını parse eder"""
        try:
            # ✅ EĞER response zaten dict ise direkt döndür
            if isinstance(response, dict):
                return response
            
            # ✅ String ise temizle ve parse et
            if isinstance(response, str):
                response = response.strip()
                if response.startswith("```json"):
                    response = response[7:]
                if response.startswith("```"):
                    response = response[3:]
                if response.endswith("```"):
                    response = response[:-3]
                response = response.strip()
                return json.loads(response)
            
            # ✅ Hiçbiri değilse hata fırlat
            raise ValueError(f"Beklenmeyen response tipi: {type(response)}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Executive JSON parse hatası: {e}")
            return {
                "summary": "Executive özet parse edilemedi.",
                "company_direction": "Bilinmiyor",
                "risk_trend": "Bilinmiyor",
                "key_developments": [],
                "recurring_problems": [],
                "critical_attention": [],
                "executive_recommendations": [],
                "confidence": 0.5
            }
        except Exception as e:
            logger.error(f"Executive parse hatası: {e}")
            return {
                "summary": "Executive özet parse edilemedi.",
                "company_direction": "Bilinmiyor",
                "risk_trend": "Bilinmiyor",
                "key_developments": [],
                "recurring_problems": [],
                "critical_attention": [],
                "executive_recommendations": [],
                "confidence": 0.5
            } 
