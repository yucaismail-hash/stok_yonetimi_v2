# app/analysis/ai_summary_engine.py - build_summary metodu eklendi

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.services.llm_service import get_llm_service

logger = logging.getLogger(__name__)


def get_language_from_country(country_code: str) -> str:
    """Ülke koduna göre dil belirler"""
    language_map = {
        "TR": "Türkçe",
        "US": "English",
        "GB": "English",
        "DE": "Deutsch",
        "FR": "Français",
        "IT": "Italiano",
        "ES": "Español",
        "NL": "Nederlands",
        "RU": "Русский",
        "AR": "العربية",
        "ZH": "中文",
        "JA": "日本語",
        "KO": "한국어",
        "PT": "Português",
        "PL": "Polski",
        "UK": "Українська",
        "RO": "Română",
        "EL": "Ελληνικά",
        "HE": "עברית",
        "HI": "हिन्दी",
    }
    return language_map.get(country_code.upper(), "English")


class AISummaryEngine:
    def __init__(self, language: str = "English"):
        self.llm = get_llm_service()
        
        model_name = os.getenv("AI_MODEL", "gemini-3.1-flash-lite")
        self.ai_version = f"{model_name}-v1"
        self.prompt_version = "v1.0"
        self.language = language
        
        logger.info(f"🧠 AI Summary Engine başlatıldı - Model: {model_name}, Dil: {language}")
    
    def build_summary(self, result_type: str, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ana metod - result_type'a göre ilgili özet metodunu çağırır.
        
        Args:
            result_type: Analiz türü (forecast_batch, safety_stock_batch, etc.)
            result_data: Analiz sonuçları (JSON)
        
        Returns:
            {
                "manager_summary": "...",
                "overall_risk": "Low/Medium/High",
                "critical_materials": [...],
                "recommended_actions": [...],
                "statistics": {...}
            }
        """
        try:
            # 1. İstatistikleri özetle
            summary_stats = self._extract_summary_stats(result_type, result_data)
            
            # 2. Prompt oluştur
            prompt = self._build_prompt(result_type, summary_stats)
            
            # 3. LLM'ye gönder
            llm_response = self.llm.generate(prompt, temperature=0.3, max_tokens=1000)
            
            # 4. Yanıtı parse et
            ai_summary = self._parse_llm_response(llm_response)
            
            # 5. Metadata ekle
            ai_summary.update({
                "_meta": {
                    "ai_version": self.ai_version,
                    "prompt_version": self.prompt_version,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "result_type": result_type,
                    "language": self.language,
                }
            })
            
            return ai_summary
            
        except Exception as e:
            logger.error(f"AI özet oluşturma hatası: {e}")
            return {
                "manager_summary": "AI özet oluşturulamadı. Lütfen daha sonra tekrar deneyin.",
                "overall_risk": "Unknown",
                "critical_materials": [],
                "recommended_actions": ["AI özet oluşturulamadı. Sistem yöneticisine başvurun."],
                "statistics": {},
                "_error": str(e)
            }
    
    def _extract_summary_stats(self, result_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """result_data'dan istatistikleri çıkarır"""
        stats = {
            "analysis_type": result_type,
            "total_items": 0,
        }
        
        if "forecast" in result_type:
            stats.update(self._extract_forecast_stats(data))
        elif "safety_stock" in result_type:
            stats.update(self._extract_safety_stock_stats(data))
        elif "simulation" in result_type:
            stats.update(self._extract_simulation_stats(data))
        elif "backtest" in result_type:
            stats.update(self._extract_backtest_stats(data))
        elif "supplier" in result_type:
            stats.update(self._extract_supplier_stats(data))
        else:
            results = data.get("results", [])
            stats["total_items"] = len(results)
            stats["results_sample"] = results[:5] if results else []
        
        return stats
    
    def _extract_forecast_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast sonuçlarından istatistik çıkarır"""
        results = data.get("results", [])
        total = len(results)
        
        if total == 0:
            return {"total_items": 0, "error": "Sonuç yok"}
        
        model_count = {}
        rmse_values = []
        trend_up = 0
        trend_down = 0
        outlier_count = 0
        pattern_dist = {}
        
        for r in results:
            model = r.get("selected_model", "unknown")
            model_count[model] = model_count.get(model, 0) + 1
            
            rmse = r.get("model_rmse")
            if rmse and rmse < 999:
                rmse_values.append(rmse)
            
            trend = r.get("trend_direction", "")
            if trend == "Artış":
                trend_up += 1
            elif trend == "Azalış":
                trend_down += 1
            
            if r.get("outlier_info", {}).get("has_outliers"):
                outlier_count += 1
            
            pattern = r.get("pattern", "DEGISKEN")
            pattern_dist[pattern] = pattern_dist.get(pattern, 0) + 1
        
        most_used_model = max(model_count.items(), key=lambda x: x[1])[0] if model_count else "auto"
        avg_rmse = sum(rmse_values) / len(rmse_values) if rmse_values else None
        
        model_labels = {
            "holt_winters": "Holt-Winters (Mevsimsel)",
            "arima": "ARIMA (Otoregresif)",
            "simple": "Basit (MA+Trend)",
            "auto": "Otomatik Seçim"
        }
        
        return {
            "total_items": total,
            "model_distribution": {model_labels.get(k, k): v for k, v in model_count.items()},
            "most_used_model": model_labels.get(most_used_model, most_used_model),
            "avg_rmse": round(avg_rmse, 2) if avg_rmse else None,
            "trend_up_count": trend_up,
            "trend_down_count": trend_down,
            "outlier_count": outlier_count,
            "pattern_distribution": pattern_dist,
        }
    
    def _extract_safety_stock_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Safety Stock sonuçlarından istatistik çıkarır"""
        results = data.get("results", [])
        total = len(results)
        
        if total == 0:
            return {"total_items": 0, "error": "Sonuç yok"}
        
        method_count = {}
        pattern_dist = {}
        abc_dist = {}
        xyz_dist = {}
        risk_high = 0
        risk_medium = 0
        risk_low = 0
        intermittent_count = 0
        seasonal_count = 0
        cv_values = []
        hybrid_ss_values = []
        
        for r in results:
            method = r.get("recommended_method", "hybrid_ss")
            method_count[method] = method_count.get(method, 0) + 1
            
            pattern = r.get("pattern", "DEGISKEN")
            pattern_dist[pattern] = pattern_dist.get(pattern, 0) + 1
            
            abc = r.get("abc", "C")
            abc_dist[abc] = abc_dist.get(abc, 0) + 1
            
            xyz = r.get("xyz", "Z")
            xyz_dist[xyz] = xyz_dist.get(xyz, 0) + 1
            
            risk = r.get("risk_level", "Düşük")
            if risk == "Yüksek":
                risk_high += 1
            elif risk == "Orta":
                risk_medium += 1
            else:
                risk_low += 1
            
            if r.get("is_intermittent"):
                intermittent_count += 1
            
            if r.get("has_seasonality"):
                seasonal_count += 1
            
            cv = r.get("cv", 0)
            if cv:
                cv_values.append(cv)
            
            hybrid_ss = r.get("hybrid_ss", 0)
            if hybrid_ss:
                hybrid_ss_values.append(hybrid_ss)
        
        method_labels = {
            "classic_ss": "Klasik SS",
            "croston_ss": "Croston SS",
            "syntetos_boylan_ss": "Syntetos-Boylan SS",
            "bootstrapping_ss": "Bootstrapping SS",
            "ml_ss": "ML Tabanlı SS",
            "hybrid_ss": "Hibrit SS (Önerilen)"
        }
        
        most_used_method = max(method_count.items(), key=lambda x: x[1])[0] if method_count else "hybrid_ss"
        
        return {
            "total_items": total,
            "method_distribution": {method_labels.get(k, k): v for k, v in method_count.items()},
            "most_used_method": method_labels.get(most_used_method, most_used_method),
            "pattern_distribution": pattern_dist,
            "abc_distribution": abc_dist,
            "xyz_distribution": xyz_dist,
            "risk_high": risk_high,
            "risk_medium": risk_medium,
            "risk_low": risk_low,
            "intermittent_count": intermittent_count,
            "seasonal_count": seasonal_count,
            "avg_cv": round(sum(cv_values) / len(cv_values), 4) if cv_values else 0,
            "avg_hybrid_ss": round(sum(hybrid_ss_values) / len(hybrid_ss_values), 0) if hybrid_ss_values else 0,
        }
    
    def _extract_simulation_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Simülasyon sonuçlarından istatistik çıkarır"""
        results = data.get("results", [])
        total = len(results)
        
        if total == 0:
            return {"total_items": 0, "error": "Sonuç yok"}
        
        service_levels = []
        cvar_values = []
        tail_risk_values = []
        high_risk = 0
        regime_count = 0
        copula_count = 0
        adaptive_count = 0
        
        for r in results:
            service_levels.append(r.get("service_level", 0))
            cvar_values.append(r.get("cvar_95", 0))
            
            tail_risk = r.get("tail_risk", 0)
            tail_risk_values.append(tail_risk)
            if tail_risk > 0.5:
                high_risk += 1
            
            if r.get("regime_used"):
                regime_count += 1
            if r.get("copula_used"):
                copula_count += 1
            if r.get("adaptive_ss_used"):
                adaptive_count += 1
        
        return {
            "total_items": total,
            "avg_service_level": round(sum(service_levels) / len(service_levels), 1),
            "min_service_level": round(min(service_levels), 1),
            "max_service_level": round(max(service_levels), 1),
            "avg_cvar_95": round(sum(cvar_values) / len(cvar_values), 1),
            "avg_tail_risk": round(sum(tail_risk_values) / len(tail_risk_values), 3),
            "high_risk_count": high_risk,
            "regime_used_count": regime_count,
            "copula_used_count": copula_count,
            "adaptive_ss_used_count": adaptive_count,
        }
    
    def _extract_backtest_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Backtest sonuçlarından istatistik çıkarır"""
        results = data.get("results", [])
        total = len(results)
        
        if total == 0:
            return {"total_items": 0, "error": "Sonuç yok"}
        
        strategy_count = {}
        service_levels = []
        total_costs = []
        tail_risk_values = []
        high_risk = 0
        
        for r in results:
            strategy = r.get("best_strategy", "hybrid")
            strategy_count[strategy] = strategy_count.get(strategy, 0) + 1
            
            service_levels.append(r.get("service_level", 0) * 100)
            total_costs.append(r.get("total_cost", 0))
            
            tail_risk = r.get("tail_risk", 0)
            tail_risk_values.append(tail_risk)
            if tail_risk > 0.5:
                high_risk += 1
        
        strategy_labels = {
            "ai": "AI",
            "classic": "Klasik",
            "croston": "Croston",
            "syntetos_boylan": "Syntetos-Boylan",
            "ml": "ML",
            "hybrid": "Hibrit",
            "simple_moving_avg": "Basit MA",
            "last_value": "Naif"
        }
        
        most_used_strategy = max(strategy_count.items(), key=lambda x: x[1])[0] if strategy_count else "hybrid"
        
        return {
            "total_items": total,
            "strategy_distribution": {strategy_labels.get(k, k): v for k, v in strategy_count.items()},
            "most_used_strategy": strategy_labels.get(most_used_strategy, most_used_strategy),
            "avg_service_level": round(sum(service_levels) / len(service_levels), 1),
            "min_service_level": round(min(service_levels), 1),
            "max_service_level": round(max(service_levels), 1),
            "avg_total_cost": round(sum(total_costs) / len(total_costs), 0),
            "avg_tail_risk": round(sum(tail_risk_values) / len(tail_risk_values), 3),
            "high_risk_count": high_risk,
        }
    
    def _extract_supplier_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Tedarikçi analizi sonuçlarından istatistik çıkarır"""
        suppliers = data.get("suppliers", [])
        total = len(suppliers)
        
        if total == 0:
            return {"total_items": 0, "error": "Sonuç yok"}
        
        risk_scores = []
        perf_scores = []
        ontime_rates = []
        high_risk = 0
        medium_risk = 0
        low_risk = 0
        good_perf = 0
        medium_perf = 0
        bad_perf = 0
        
        for s in suppliers:
            risk_scores.append(s.get("risk_score", 0))
            perf_scores.append(s.get("performance_score", 0))
            ontime_rates.append(s.get("ontime_rate", 0))
            
            risk_level = s.get("risk_level", "DÜŞÜK")
            if risk_level == "YÜKSEK":
                high_risk += 1
            elif risk_level == "ORTA":
                medium_risk += 1
            else:
                low_risk += 1
            
            perf_level = s.get("performance_level", "ORTA")
            if perf_level == "İYİ":
                good_perf += 1
            elif perf_level == "ORTA":
                medium_perf += 1
            else:
                bad_perf += 1
        
        return {
            "total_items": total,
            "avg_risk_score": round(sum(risk_scores) / len(risk_scores), 3),
            "avg_performance_score": round(sum(perf_scores) / len(perf_scores), 3),
            "avg_ontime_rate": round(sum(ontime_rates) / len(ontime_rates), 1),
            "high_risk_count": high_risk,
            "medium_risk_count": medium_risk,
            "low_risk_count": low_risk,
            "good_performance_count": good_perf,
            "medium_performance_count": medium_perf,
            "bad_performance_count": bad_perf,
        }
    
    def _build_prompt(self, result_type: str, stats: Dict[str, Any]) -> str:
        """İstatistiklerden prompt oluşturur - DİL DESTEKLİ"""
        
        language_instructions = {
            "Türkçe": """
Lütfen tüm yanıtlarını TÜRKÇE olarak ver.
Profesyonel bir tedarik zinciri danışmanı gibi konuş.
Yönetici özeti, risk analizi ve aksiyon önerileri Türkçe olsun.
""",
            "English": """
Please respond in ENGLISH.
Speak like a professional supply chain consultant.
All executive summary, risk analysis, and recommendations must be in English.
""",
            "Deutsch": """
Bitte antworte auf DEUTSCH.
Sprich wie ein professioneller Supply-Chain-Berater.
Alle Zusammenfassungen, Risikoanalysen und Empfehlungen müssen auf Deutsch sein.
""",
            "Français": """
Veuillez répondre en FRANÇAIS.
Parlez comme un consultant professionnel en chaîne d'approvisionnement.
Tous les résumés, analyses de risques et recommandations doivent être en français.
""",
            "Italiano": """
Rispondi in ITALIANO.
Parla come un consulente professionale della supply chain.
Tutti i riassunti, le analisi dei rischi e le raccomandazioni devono essere in italiano.
""",
            "Español": """
Por favor responde en ESPAÑOL.
Habla como un consultor profesional de la cadena de suministro.
Todos los resúmenes, análisis de riesgos y recomendaciones deben estar en español.
""",
        }
        
        language_instruction = language_instructions.get(self.language, language_instructions["English"])
        
        type_titles = {
            "forecast_batch": "Talep Tahmini Analizi" if self.language == "Türkçe" else "Demand Forecast Analysis",
            "forecast_batch_async": "Talep Tahmini Analizi" if self.language == "Türkçe" else "Demand Forecast Analysis",
            "safety_stock_batch": "Emniyet Stoğu Analizi" if self.language == "Türkçe" else "Safety Stock Analysis",
            "safety_stock_batch_async": "Emniyet Stoğu Analizi" if self.language == "Türkçe" else "Safety Stock Analysis",
            "simulation_batch": "Monte Carlo Simülasyon Analizi" if self.language == "Türkçe" else "Monte Carlo Simulation Analysis",
            "simulation_batch_async": "Monte Carlo Simülasyon Analizi" if self.language == "Türkçe" else "Monte Carlo Simulation Analysis",
            "backtest_batch": "Backtest Analizi" if self.language == "Türkçe" else "Backtest Analysis",
            "backtest_batch_async": "Backtest Analizi" if self.language == "Türkçe" else "Backtest Analysis",
            "supplier_batch": "Tedarikçi Performans Analizi" if self.language == "Türkçe" else "Supplier Performance Analysis",
            "supplier_batch_async": "Tedarikçi Performans Analizi" if self.language == "Türkçe" else "Supplier Performance Analysis",
        }
        title = type_titles.get(result_type, "Analiz Raporu" if self.language == "Türkçe" else "Analysis Report")
        
        prompt = f"""
{language_instruction}

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
3. Identify critical materials or suppliers that need immediate attention (max 5).
4. Suggest actionable recommendations (max 5) for the operations team.
5. Include key statistics in a structured format.

**Response Format (JSON):**
{{
  "manager_summary": "Executive summary text",
  "overall_risk": "Low|Medium|High",
  "critical_materials": ["material_code1", "material_code2", ...],
  "recommended_actions": ["action1", "action2", ...],
  "statistics": {{
    "key1": "value1",
    "key2": "value2"
  }}
}}

**IMPORTANT:** Return ONLY valid JSON. No additional text outside the JSON.
"""
        return prompt
    
    # app/analysis/ai_summary_engine.py - _parse_llm_response metodunu güncelle

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """LLM yanıtını parse eder - GENİŞLETİLMİŞ JSON YAPISI"""
        try:
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()
            
            data = json.loads(response)
            
            # Zorunlu alanlar
            required_fields = ["manager_summary", "overall_risk", "critical_materials", "recommended_actions"]
            for field in required_fields:
                if field not in data:
                    data[field] = "Veri mevcut değil" if field == "manager_summary" else []
            
            # ✅ YENİ: Genişletilmiş JSON yapısı
            enhanced_data = {
                "summary": data.get("manager_summary", ""),
                "key_points": data.get("key_points", []),
                "risks": data.get("risks", []),
                "opportunities": data.get("opportunities", []),
                "recommendations": data.get("recommended_actions", []),
                "executive_points": data.get("executive_points", []),
                "kpis": data.get("statistics", {}),
                "overall_risk": data.get("overall_risk", "Unknown"),
                "critical_materials": data.get("critical_materials", []),
                "confidence": data.get("confidence", 0.85),
                "_meta": data.get("_meta", {})
            }
            
            return enhanced_data
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse hatası: {e}")
            return {
                "summary": response[:500] if response else "LLM yanıtı parse edilemedi.",
                "key_points": [],
                "risks": [],
                "opportunities": [],
                "recommendations": ["LLM yanıtı parse edilemedi. Lütfen tekrar deneyin."],
                "executive_points": [],
                "kpis": {},
                "overall_risk": "Unknown",
                "critical_materials": [],
                "confidence": 0.5,
                "_parse_error": str(e)
            }

    def executive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Birden fazla analiz sonucundan yönetici özeti oluşturur."""
        if not analysis_results:
            return {
                "manager_summary": "Henüz analiz sonucu bulunmuyor. Lütfen ilk analizinizi yapın.",
                "overall_risk": "Unknown",
                "critical_materials": [],
                "recommended_actions": ["Henüz analiz yok. Stokonomi ile analiz yapmaya başlayın."],
                "statistics": {"total_analyses": 0}
            }
        
        total_analyses = len(analysis_results)
        total_materials = 0
        all_risks = []
        all_recommendations = []
        all_critical = []
        
        for result in analysis_results:
            ai_summary = result.get("ai_summary", {})
            if ai_summary:
                total_materials += ai_summary.get("statistics", {}).get("total_items", 0)
                all_risks.append(ai_summary.get("overall_risk", "Medium"))
                all_recommendations.extend(ai_summary.get("recommended_actions", []))
                all_critical.extend(ai_summary.get("critical_materials", []))
        
        risk_counts = {"Low": 0, "Medium": 0, "High": 0}
        for risk in all_risks:
            if risk in risk_counts:
                risk_counts[risk] += 1
        
        if risk_counts["High"] > 0:
            overall_risk = "High"
        elif risk_counts["Medium"] > 0:
            overall_risk = "Medium"
        else:
            overall_risk = "Low"
        
        unique_critical = list(set(all_critical))[:5]
        unique_actions = list(set(all_recommendations))[:5]
        
        exec_prompt = f"""
You are a senior Supply Chain Consultant preparing an executive dashboard summary.

**Summary of all analyses:**
- Total analyses: {total_analyses}
- Total materials analyzed: {total_materials}
- Risk distribution: {risk_counts}
- Overall risk level: {overall_risk}

**Critical materials: {unique_critical}**
**Key actions: {unique_actions}**

Provide a concise executive summary (max 3 sentences) that captures the overall health of the supply chain.

Response JSON format:
{{
  "manager_summary": "Executive summary text (max 3 sentences)",
  "overall_risk": "{overall_risk}",
  "critical_materials": {json.dumps(unique_critical)},
  "recommended_actions": {json.dumps(unique_actions)},
  "statistics": {{
    "total_analyses": {total_analyses},
    "total_materials": {total_materials},
    "risk_distribution": {json.dumps(risk_counts)}
  }}
}}
"""
        
        try:
            response = self.llm.generate(exec_prompt, temperature=0.2, max_tokens=400)
            return self._parse_llm_response(response)
        except Exception as e:
            logger.error(f"Executive summary oluşturma hatası: {e}")
            return {
                "manager_summary": f"{total_analyses} analiz tamamlandı. Toplam {total_materials} ürün analiz edildi.",
                "overall_risk": overall_risk,
                "critical_materials": unique_critical,
                "recommended_actions": unique_actions,
                "statistics": {
                    "total_analyses": total_analyses,
                    "total_materials": total_materials,
                    "risk_distribution": risk_counts
                }
            }