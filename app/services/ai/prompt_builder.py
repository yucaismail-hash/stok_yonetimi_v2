# app/services/ai/prompt_builder.py

import json
from typing import Dict, Any, Optional

from .config import AIConfig


class PromptBuilder:
    """
    Prompt Builder - Tüm prompt'lar burada üretilir.
    
    Hiçbir provider içinde prompt yazılmaz.
    Tüm prompt'lar buradan gelir.
    """
    
    def __init__(self, language: str = "English"):
        self.language = language
    
    def build_safety_stock_prompt(self, stats: Dict[str, Any]) -> str:
        """Safety Stock analizi için prompt oluşturur"""
        return self._build_prompt("safety_stock", stats)
    
    def build_forecast_prompt(self, stats: Dict[str, Any]) -> str:
        """Forecast analizi için prompt oluşturur"""
        return self._build_prompt("forecast", stats)
    
    def build_simulation_prompt(self, stats: Dict[str, Any]) -> str:
        """Simülasyon analizi için prompt oluşturur"""
        return self._build_prompt("simulation", stats)
    
    def build_backtest_prompt(self, stats: Dict[str, Any]) -> str:
        """Backtest analizi için prompt oluşturur"""
        return self._build_prompt("backtest", stats)
    
    def build_supplier_prompt(self, stats: Dict[str, Any]) -> str:
        """Tedarikçi analizi için prompt oluşturur"""
        return self._build_prompt("supplier", stats)
    
    def build_trend_prompt(self, stats: Dict[str, Any]) -> str:
        """Trend analizi için prompt oluşturur"""
        return self._build_prompt("trend", stats)
    
    def build_executive_prompt(self, stats: Dict[str, Any]) -> str:
        """Executive özet için prompt oluşturur"""
        return self._build_prompt("executive", stats)
    
    def _build_prompt(self, prompt_type: str, stats: Dict[str, Any]) -> str:
        """Genel prompt oluşturma metodu"""
        
        # Dil talimatları
        language_instructions = {
            "Türkçe": "Lütfen tüm yanıtlarını TÜRKÇE olarak ver. Profesyonel bir tedarik zinciri danışmanı gibi konuş.",
            "English": "Please respond in ENGLISH. Speak like a professional supply chain consultant.",
            "Deutsch": "Bitte antworte auf DEUTSCH. Sprich wie ein professioneller Supply-Chain-Berater.",
            "Français": "Veuillez répondre en FRANÇAIS. Parlez comme un consultant professionnel en chaîne d'approvisionnement.",
        }
        lang_instruction = language_instructions.get(self.language, language_instructions["English"])
        
        # Prompt türüne göre başlık
        titles = {
            "safety_stock": "Safety Stock Analysis",
            "forecast": "Demand Forecast Analysis",
            "simulation": "Monte Carlo Simulation Analysis",
            "backtest": "Backtest Analysis",
            "supplier": "Supplier Performance Analysis",
            "trend": "Trend Analysis",
            "executive": "Executive Summary",
        }
        title = titles.get(prompt_type, "Analysis Report")
        
        # JSON format talimatları
        json_format = {
            "safety_stock": {
                "manager_summary": "Executive summary (2-3 sentences)",
                "overall_risk": "Low|Medium|High",
                "critical_materials": ["material_code1", "material_code2"],
                "recommended_actions": ["action1", "action2"],
                "confidence_score": 0.95,
            },
            "forecast": {
                "manager_summary": "Executive summary (2-3 sentences)",
                "overall_risk": "Low|Medium|High",
                "key_findings": ["finding1", "finding2"],
                "recommended_actions": ["action1", "action2"],
                "confidence_score": 0.95,
            },
            "simulation": {
                "manager_summary": "Executive summary (2-3 sentences)",
                "overall_risk": "Low|Medium|High",
                "critical_materials": ["material_code1", "material_code2"],
                "recommended_actions": ["action1", "action2"],
                "confidence_score": 0.95,
            },
            "backtest": {
                "manager_summary": "Executive summary (2-3 sentences)",
                "overall_risk": "Low|Medium|High",
                "best_strategies": ["strategy1", "strategy2"],
                "recommended_actions": ["action1", "action2"],
                "confidence_score": 0.95,
            },
            "supplier": {
                "manager_summary": "Executive summary (2-3 sentences)",
                "overall_risk": "Low|Medium|High",
                "critical_suppliers": ["supplier1", "supplier2"],
                "recommended_actions": ["action1", "action2"],
                "confidence_score": 0.95,
            },
            "trend": {
                "summary": "Trend summary (2-3 sentences)",
                "trend_direction": "Improving|Stable|Deteriorating",
                "risk_trend": "Decreasing|Stable|Increasing",
                "key_insights": ["insight1", "insight2"],
                "recurring_issues": ["issue1", "issue2"],
                "executive_recommendations": ["rec1", "rec2"],
                "confidence_score": 0.95,
            },
            "executive": {
                "summary": "Executive summary (2-3 sentences)",
                "company_direction": "Improving|Stable|Deteriorating",
                "risk_trend": "Decreasing|Stable|Increasing",
                "key_developments": ["dev1", "dev2"],
                "critical_attention": ["attention1", "attention2"],
                "executive_recommendations": ["rec1", "rec2"],
                "confidence_score": 0.95,
            },
        }
        
        json_example = json_format.get(prompt_type, json_format["safety_stock"])
        
        prompt = f"""
{lang_instruction}

You are a senior Supply Chain Consultant with 20+ years of experience.

**CRITICAL RULES:**
- DO NOT calculate any inventory values, safety stock, or forecast numbers.
- DO NOT generate new numbers or statistics.
- ONLY use the provided analysis results and statistics.
- Your task is to INTERPRET and EXPLAIN the results in a professional manner.
- Act as a senior consultant presenting findings to the C-suite.

**Analysis Report: {title}**

**Summary Statistics:**
{json.dumps(stats, indent=2, ensure_ascii=False)}

**Your Task:**
1. Provide a concise executive summary (2-3 sentences) that captures the most important insights.
2. Assess the overall risk level (Low/Medium/High) based on the data.
3. Identify critical items that need immediate attention (max 5).
4. Suggest actionable recommendations (max 5).
5. Provide a confidence score (0-1).

**Response Format (JSON):**
{json.dumps(json_example, indent=2)}

**IMPORTANT:** Return ONLY valid JSON. No additional text outside the JSON.
"""
        return prompt