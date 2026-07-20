# app/analysis/ai_summary_engine.py - YENİ MİMARİ İLE GÜNCELLENDİ

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# ✅ YENİ: Yeni AI mimarisinden import et
from app.services.ai import get_llm_service, PromptBuilder, AIProviderError, AIJSONParseError
from app.services.ai.config import AIConfig

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
    """
    AI Summary Engine - Yeni AI mimarisi ile
    
    Görevleri:
    1. Prompt Builder'dan prompt al
    2. LLM Service'e gönder (Provider Manager üzerinden)
    3. JSON parse et
    4. Database'e kaydet
    """
    
    def __init__(self, language: str = "English"):
        self.language = language
        self.llm_service = get_llm_service()  # ✅ YENİ: LLM Service
        self.prompt_builder = PromptBuilder(language=language)  # ✅ YENİ: Prompt Builder
        
        model_name = os.getenv("AI_MODEL", "gemini-3.1-flash-lite")
        provider = os.getenv("AI_PROVIDER", "gemini")
        self.ai_version = f"{provider}-{model_name}-v1"
        self.prompt_version = "v1.0"
        
        logger.info(f"🧠 AI Summary Engine başlatıldı - Provider: {provider}, Model: {model_name}, Dil: {language}")
    
    def build_summary(self, result_type: str, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ana metod - result_type'a göre ilgili özet metodunu çağırır.
        
        Args:
            result_type: Analiz türü (forecast_batch, safety_stock_batch, etc.)
            result_data: Analiz sonuçları (JSON)
        
        Returns:
            {
                "summary": "...",
                "overall_risk": "Low/Medium/High",
                "critical_materials": [...],
                "recommendations": [...],
                "kpis": {...},
                "confidence": 0.95
            }
        """
        try:
            # 1. İstatistikleri özetle
            summary_stats = self._extract_summary_stats(result_type, result_data)
            
            # 2. Prompt Builder'dan prompt al
            prompt = self._get_prompt(result_type, summary_stats)
            
            # 3. LLM Service'e gönder (JSON yanıt bekliyor)
            ai_summary = self.llm_service.generate_json(
                prompt,
                temperature=0.3,
                max_tokens=AIConfig.MAX_TOKENS
            )
            
            # 4. Metadata ekle
            ai_summary["_meta"] = {
                "ai_version": self.ai_version,
                "prompt_version": self.prompt_version,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "result_type": result_type,
                "language": self.language,
                "provider": AIConfig.PROVIDER,
                "model": AIConfig.MODEL,
            }
            
            return ai_summary
            
        except AIJSONParseError as e:
            logger.error(f"JSON parse hatası: {e}")
            return self._get_fallback_response(str(e))
        except AIProviderError as e:
            logger.error(f"AI Provider hatası: {e}")
            return self._get_fallback_response(str(e))
        except Exception as e:
            logger.error(f"Beklenmeyen hata: {e}")
            return self._get_fallback_response(str(e))
    
    def _get_prompt(self, result_type: str, stats: Dict[str, Any]) -> str:
        """Result type'a göre Prompt Builder'dan prompt alır"""
        # result_type'ı normalize et
        key = result_type.split("_")[0] if "_" in result_type else result_type
        
        prompt_methods = {
            "safety_stock": self.prompt_builder.build_safety_stock_prompt,
            "forecast": self.prompt_builder.build_forecast_prompt,
            "simulation": self.prompt_builder.build_simulation_prompt,
            "backtest": self.prompt_builder.build_backtest_prompt,
            "supplier": self.prompt_builder.build_supplier_prompt,
        }
        
        builder = prompt_methods.get(key, self.prompt_builder.build_safety_stock_prompt)
        return builder(stats)
    
    def _get_fallback_response(self, error: str) -> Dict[str, Any]:
        """Hata durumunda fallback yanıtı döndürür"""
        return {
            "summary": "AI özeti oluşturulamadı. Lütfen daha sonra tekrar deneyin.",
            "overall_risk": "Unknown",
            "critical_materials": [],
            "recommendations": ["AI özeti oluşturulamadı. Sistem yöneticisine başvurun."],
            "kpis": {},
            "confidence": 0.0,
            "_error": error,
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

    def executive_summary(self, analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Birden fazla analiz sonucundan yönetici özeti oluşturur.
        Dashboard için kullanılır.
        """
        if not analysis_results:
            return {
                "summary": "Henüz analiz sonucu bulunmuyor. Lütfen ilk analizinizi yapın.",
                "overall_risk": "Unknown",
                "critical_materials": [],
                "recommendations": ["Henüz analiz yok. Stokonomi ile analiz yapmaya başlayın."],
                "kpis": {"total_analyses": 0},
                "confidence": 0.0
            }
        
        total_analyses = len(analysis_results)
        total_materials = 0
        all_risks = []
        all_recommendations = []
        all_critical = []
        
        for result in analysis_results:
            ai_summary = result.get("ai_summary", {})
            if ai_summary:
                kpis = ai_summary.get("kpis", {})
                total_materials += kpis.get("total_items", 0)
                all_risks.append(ai_summary.get("overall_risk", "Medium"))
                all_recommendations.extend(ai_summary.get("recommendations", []))
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
        
        # Prompt Builder'dan executive prompt al
        stats = {
            "total_analyses": total_analyses,
            "total_materials": total_materials,
            "risk_distribution": risk_counts,
            "overall_risk": overall_risk,
            "critical_materials": unique_critical,
            "recommendations": unique_actions,
        }
        
        prompt = self.prompt_builder.build_executive_prompt(stats)
        
        try:
            result = self.llm_service.generate_json(prompt, temperature=0.2, max_tokens=400)
            result["_meta"] = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source": "executive_summary",
                "analyses_used": total_analyses,
            }
            return result
        except Exception as e:
            logger.error(f"Executive summary oluşturma hatası: {e}")
            return {
                "summary": f"{total_analyses} analiz tamamlandı. Toplam {total_materials} ürün analiz edildi.",
                "overall_risk": overall_risk,
                "critical_materials": unique_critical,
                "recommendations": unique_actions,
                "kpis": {
                    "total_analyses": total_analyses,
                    "total_materials": total_materials,
                    "risk_distribution": risk_counts
                },
                "confidence": 0.5,
                "_error": str(e)
            }