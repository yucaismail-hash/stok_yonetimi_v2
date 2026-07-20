# app/analysis/trend_summary_engine.py - YENİ DOSYA

"""
Trend Summary Engine - Son analizlerden trend çıkarır
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import AnalysisResult, User
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country

logger = logging.getLogger(__name__)


class TrendSummaryEngine:
    """
    Trend Summary - Son analizlerden trend çıkarır
    """
    
    def __init__(self, language: str = "English"):
        self.language = language
        self.ai_engine = AISummaryEngine(language=language)
        self.max_analyses = 5
        self.max_days = 30
    
    def get_recent_analyses(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Son 30 gün içindeki analizleri getir (max 5)
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_days)
        
        analyses = db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user_id,
            AnalysisResult.created_at >= cutoff_date,
            AnalysisResult.ai_summary.isnot(None)
        ).order_by(
            AnalysisResult.created_at.desc()
        ).limit(self.max_analyses).all()
        
        return [
            {
                "id": a.id,
                "result_type": a.result_type,
                "created_at": a.created_at.isoformat(),
                "ai_summary": a.ai_summary
            }
            for a in analyses
        ]
    
    def build_trend_summary(self, analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analiz özetlerinden trend summary oluşturur
        """
        if not analyses:
            return {
                "summary": "Henüz yeterli analiz verisi yok.",
                "trend_direction": "Bilinmiyor",
                "risk_trend": "Bilinmiyor",
                "key_insights": [],
                "recurring_issues": [],
                "improvements": [],
                "executive_recommendations": [],
                "kpis": {},
                "confidence": 0.0,
                "_meta": {
                    "analyses_used": 0,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
        
        # Analiz özetlerinden veri çıkar
        all_risks = []
        all_recommendations = []
        all_insights = []
        all_kpis = {}
        risk_levels = []
        
        for analysis in analyses:
            ai_summary = analysis.get("ai_summary", {})
            if not ai_summary:
                continue
            
            # Riskler
            risks = ai_summary.get("risks", [])
            all_risks.extend(risks)
            
            # Tavsiyeler
            recommendations = ai_summary.get("recommendations", [])
            all_recommendations.extend(recommendations)
            
            # KPIs
            kpis = ai_summary.get("kpis", {})
            for key, value in kpis.items():
                if key not in all_kpis:
                    all_kpis[key] = []
                all_kpis[key].append(value)
            
            # Risk seviyesi
            risk = ai_summary.get("overall_risk", "Medium")
            risk_levels.append(risk)
        
        # Trend analizi
        risk_trend = self._calculate_risk_trend(risk_levels)
        
        # Tekrarlayan problemler
        recurring_issues = self._find_recurring_issues(all_risks)
        
        # İyileşmeler
        improvements = self._find_improvements(analyses)
        
        # KPI ortalamaları
        avg_kpis = {}
        for key, values in all_kpis.items():
            if values:
                avg_kpis[key] = sum(values) / len(values)
        
        # Prompt oluştur
        prompt = self._build_trend_prompt(
            analyses_count=len(analyses),
            risk_trend=risk_trend,
            recurring_issues=recurring_issues,
            improvements=improvements,
            avg_kpis=avg_kpis,
            all_recommendations=all_recommendations[:5]
        )
        
        # AI çağır
        try:
            response = self.ai_engine.llm.generate(prompt, temperature=0.3, max_tokens=800)
            result = self._parse_trend_response(response)
            
            # Metadata ekle
            result["_meta"] = {
                "analyses_used": len(analyses),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "ai_version": self.ai_engine.ai_version,
                "prompt_version": self.ai_engine.prompt_version,
                "language": self.language
            }
            result["kpis"] = avg_kpis
            
            return result
            
        except Exception as e:
            logger.error(f"Trend summary oluşturma hatası: {e}")
            return {
                "summary": f"{len(analyses)} analiz değerlendirildi.",
                "trend_direction": "Bilinmiyor",
                "risk_trend": risk_trend,
                "key_insights": all_insights[:5],
                "recurring_issues": recurring_issues[:3],
                "improvements": improvements[:3],
                "executive_recommendations": all_recommendations[:3],
                "kpis": avg_kpis,
                "confidence": 0.5,
                "_meta": {
                    "analyses_used": len(analyses),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "error": str(e)
                }
            }
    
    def _calculate_risk_trend(self, risk_levels: List[str]) -> str:
        """Risk trendini hesaplar"""
        if len(risk_levels) < 2:
            return "Bilinmiyor"
        
        risk_values = {"Low": 1, "Medium": 2, "High": 3}
        values = [risk_values.get(r, 2) for r in risk_levels]
        
        if len(values) >= 2:
            if values[0] > values[-1]:
                return "Azalıyor"
            elif values[0] < values[-1]:
                return "Artıyor"
        
        return "Stabil"
    
    def _find_recurring_issues(self, risks: List[str]) -> List[str]:
        """Tekrarlayan problemleri bulur"""
        from collections import Counter
        if not risks:
            return []
        
        counter = Counter(risks)
        return [issue for issue, count in counter.most_common(5) if count > 1]
    
    def _find_improvements(self, analyses: List[Dict]) -> List[str]:
        """İyileşmeleri bulur"""
        improvements = []
        for a in analyses:
            ai_summary = a.get("ai_summary", {})
            opps = ai_summary.get("opportunities", [])
            improvements.extend(opps)
        return improvements[:5]
    
    def _build_trend_prompt(self, **kwargs) -> str:
        """Trend summary prompt oluşturur"""
        language_instructions = {
            "Türkçe": "Lütfen tüm yanıtlarını TÜRKÇE olarak ver.",
            "English": "Please respond in ENGLISH.",
        }
        lang_instruction = language_instructions.get(self.language, language_instructions["English"])
        
        return f"""
{lang_instruction}

You are a senior Supply Chain Consultant analyzing trends across multiple analyses.

**Analysis Summary:**
- Total analyses reviewed: {kwargs.get('analyses_count', 0)}
- Risk trend: {kwargs.get('risk_trend', 'Bilinmiyor')}
- Recurring issues: {kwargs.get('recurring_issues', [])}
- Improvements identified: {kwargs.get('improvements', [])}
- Key recommendations: {kwargs.get('all_recommendations', [])}
- Average KPIs: {kwargs.get('avg_kpis', {})}

**Your Task:**
Provide a trend summary that answers:
1. What is the overall direction? (improving/stable/deteriorating)
2. Are risks increasing or decreasing?
3. What are the recurring problems?
4. What improvements have been made?
5. What should management focus on?

**Response Format (JSON):**
{{
  "summary": "Overall trend summary (2-3 sentences)",
  "trend_direction": "İyileşiyor|Stabil|Kötüleşiyor",
  "risk_trend": "Azalıyor|Stabil|Artıyor",
  "key_insights": ["insight1", "insight2", ...],
  "recurring_issues": ["issue1", "issue2", ...],
  "improvements": ["improvement1", "improvement2", ...],
  "executive_recommendations": ["rec1", "rec2", ...],
  "confidence": 0.95
}}

IMPORTANT: Return ONLY valid JSON.
"""
    
    def _parse_trend_response(self, response: str) -> Dict[str, Any]:
        """Trend yanıtını parse eder"""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Trend JSON parse hatası: {e}")
            return {
                "summary": "Trend analizi parse edilemedi.",
                "trend_direction": "Bilinmiyor",
                "risk_trend": "Bilinmiyor",
                "key_insights": [],
                "recurring_issues": [],
                "improvements": [],
                "executive_recommendations": [],
                "confidence": 0.5
            }