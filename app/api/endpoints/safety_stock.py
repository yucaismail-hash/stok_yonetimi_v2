from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country
from app.analysis.trend_summary_engine import TrendSummaryEngine
from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
from app.auth import get_current_user
from app.models import User, AnalysisResult, Notification
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import uuid
import numpy as np
import logging

from app.api.dependencies import (
    get_or_create_dataset_from_upload,
    process_pricing_with_dataset,
    get_active_dataset
)

# ✅ LOGGER
logger = logging.getLogger(__name__)

router = APIRouter()
optimizer = ComprehensiveSafetyStockOptimizer()
pattern_analyzer = AdvancedDemandAnalyzer()
ai_engine = AISummaryEngine()


# ============================================================
# 📌 AKILLI ANALİZ MOTORU - Yardımcı Fonksiyonlar
# ============================================================

def calculate_abc_xyz(material: dict, demand: list) -> dict:
    """
    ABC/XYZ analizini hesaplar.
    ABC: Maliyet bazlı (A: %70, B: %20, C: %10)
    XYZ: Talep değişkenliği bazlı (X: CV<0.3, Y: CV<0.6, Z: CV>=0.6)
    """
    unit_cost = material.get('unit_cost', 0)
    avg_demand = np.mean(demand) if demand else 0
    demand_std = np.std(demand) if demand else 0
    cv = demand_std / avg_demand if avg_demand > 0 else 0
    
    # ABC (Maliyet bazlı)
    if unit_cost > 100:
        abc = 'A'
    elif unit_cost > 30:
        abc = 'B'
    else:
        abc = 'C'
    
    # XYZ (Değişkenlik bazlı)
    if cv < 0.3:
        xyz = 'X'
    elif cv < 0.6:
        xyz = 'Y'
    else:
        xyz = 'Z'
    
    return {
        'abc': abc,
        'xyz': xyz,
        'abc_label': 'Yüksek Maliyetli' if abc == 'A' else ('Orta Maliyetli' if abc == 'B' else 'Düşük Maliyetli'),
        'xyz_label': 'Düzenli Talep' if xyz == 'X' else ('Değişken Talep' if xyz == 'Y' else 'Düzensiz Talep'),
        'abc_color': 'error' if abc == 'A' else ('warning' if abc == 'B' else 'success'),
        'xyz_color': 'success' if xyz == 'X' else ('warning' if xyz == 'Y' else 'error'),
    }


def check_seasonality(demand: list) -> dict:
    """Sezonsallık kontrolü yapar (basit yaklaşım)"""
    if len(demand) < 12:
        return {
            'has_seasonality': False,
            'seasonal_period': 0,
            'seasonality_strength': 0,
            'seasonality_label': 'Yok'
        }
    
    first_half = demand[:len(demand)//2]
    second_half = demand[len(demand)//2:]
    if len(first_half) < 6 or len(second_half) < 6:
        return {
            'has_seasonality': False,
            'seasonal_period': 0,
            'seasonality_strength': 0,
            'seasonality_label': 'Yok'
        }
    
    min_len = min(len(first_half), len(second_half))
    corr = np.corrcoef(first_half[:min_len], second_half[:min_len])[0, 1] if min_len > 1 else 0
    
    has_seasonality = bool(corr > 0.3)
    strength = float(round(max(0, corr), 2))
    
    return {
        'has_seasonality': has_seasonality,
        'seasonal_period': 12 if has_seasonality else 0,
        'seasonality_strength': strength,
        'seasonality_label': 'Güçlü Sezonsallık' if strength > 0.6 else ('Orta Sezonsallık' if strength > 0.3 else 'Zayıf Sezonsallık')
    }


def check_trend(demand: list) -> dict:
    """Trend analizi yapar"""
    if len(demand) < 4:
        return {
            'has_trend': False,
            'trend_direction': 'Yok',
            'trend_strength': 0,
            'trend_slope': 0,
            'trend_label': 'Düz'
        }
    
    x = np.arange(len(demand))
    y = np.array(demand)
    
    slope, intercept = np.polyfit(x, y, 1)
    
    slope = float(slope)
    trend_strength = float(round(abs(slope) / (np.mean(y) + 0.001), 3))
    has_trend = bool(abs(slope) > 0.01)
    
    if abs(slope) < 0.01:
        direction = 'Yok'
    elif slope > 0:
        direction = 'Artış'
    else:
        direction = 'Azalış'
    
    return {
        'has_trend': has_trend,
        'trend_direction': direction,
        'trend_strength': trend_strength,
        'trend_slope': slope,
        'trend_label': f'{direction} Eğilimi' if direction != 'Yok' else 'Düz'
    }


def check_intermittent_demand(demand: list, zero_ratio: float, cv: float) -> dict:
    if not demand:
        return {'is_intermittent': False, 'intermittent_level': 'Düzenli', 'recommendation': ''}
    
    nonzero = [d for d in demand if d > 0]
    avg_nonzero = np.mean(nonzero) if nonzero else 0
    std_nonzero = np.std(nonzero) if nonzero else 0
    adi = std_nonzero / avg_nonzero if avg_nonzero > 0 else 0
    
    is_intermittent = bool(zero_ratio > 0.3 or cv > 0.8)
    
    if zero_ratio > 0.5:
        level = 'Yüksek Aralıklı'
        recommendation = 'Croston veya Syntetos-Boylan kullanın'
    elif zero_ratio > 0.3:
        level = 'Orta Aralıklı'
        recommendation = 'Croston veya Bootstrap değerlendirin'
    elif cv > 0.8:
        level = 'Yüksek Değişken'
        recommendation = 'Bootstrap veya AI Hybrid kullanın'
    else:
        level = 'Düzenli'
        recommendation = 'Klasik SS veya Hibrit kullanın'
    
    return {
        'is_intermittent': is_intermittent,
        'intermittent_level': level,
        'zero_ratio': zero_ratio,
        'adi': float(round(adi, 2)),
        'recommendation': recommendation
    }


def get_forecast_recommendation(seasonality: dict, trend: dict, intermittent: dict, cv: float) -> dict:
    has_seasonality = seasonality.get('has_seasonality', False)
    has_trend = trend.get('has_trend', False)
    is_intermittent = intermittent.get('is_intermittent', False)
    intermittent_level = intermittent.get('intermittent_level', '')
    
    if is_intermittent:
        if intermittent_level == 'Yüksek Aralıklı':
            model = 'croston_sba'
            model_label = 'Croston SBA'
            reason = 'Yüksek aralıklı talep yapısı için özelleştirilmiş yöntem'
        else:
            model = 'croston'
            model_label = 'Croston'
            reason = 'Aralıklı talep yapısı için uygun yöntem'
    elif has_seasonality and has_trend:
        model = 'holt_winters'
        model_label = 'Holt-Winters'
        reason = 'Trend ve mevsimsellik içeren talep yapısı'
    elif has_trend:
        model = 'holt'
        model_label = 'Holt (Üstel Düzeltme)'
        reason = 'Trend içeren talep yapısı'
    elif cv < 0.3:
        model = 'simple'
        model_label = 'Basit Hareketli Ortalama'
        reason = 'Düşük değişkenlikli talep'
    else:
        model = 'auto'
        model_label = 'Otomatik (AI)'
        reason = 'Karmaşık talep yapısı, en iyi model otomatik seçilir'
    
    return {
        'model': model,
        'model_label': model_label,
        'reason': reason,
        'confidence': 'Yüksek' if cv < 0.3 else ('Orta' if cv < 0.6 else 'Düşük')
    }


def get_ss_method_recommendation(pattern: str, pattern_stats: dict, intermittent: dict) -> dict:
    cv = pattern_stats.get('cv', 0)
    zero_ratio = pattern_stats.get('zero_ratio', 0)
    
    if pattern == 'SIFIR_TALEP':
        method = 'classic_ss'
        method_label = 'Klasik SS'
        reason = 'Sıfır talep durumu, basit yaklaşım yeterli'
    elif intermittent['is_intermittent'] and zero_ratio > 0.4:
        method = 'croston_ss'
        method_label = 'Croston SS'
        reason = 'Yüksek aralıklı talep için özel yöntem'
    elif intermittent['is_intermittent']:
        method = 'syntetos_boylan_ss'
        method_label = 'Syntetos-Boylan SS'
        reason = 'Aralıklı talep için Croston\'un geliştirilmiş hali'
    elif cv > 0.7:
        method = 'bootstrapping_ss'
        method_label = 'Bootstrapping SS'
        reason = 'Yüksek değişkenlik, binlerce senaryo ile gerçekçi sonuç'
    elif cv > 0.4:
        method = 'ml_ss'
        method_label = 'ML Tabanlı SS'
        reason = 'Orta-yüksek değişkenlik, geçmiş veriden öğrenir'
    elif cv < 0.2:
        method = 'classic_ss'
        method_label = 'Klasik SS'
        reason = 'Düşük değişkenlik, normal dağılım varsayımı geçerli'
    else:
        method = 'hybrid_ss'
        method_label = 'Hibrit SS (Önerilen)'
        reason = 'Tüm yöntemlerin ortalaması, dengeli yaklaşım'
    
    return {
        'method': method,
        'method_label': method_label,
        'reason': reason,
        'confidence': 'Yüksek' if cv < 0.3 else ('Orta' if cv < 0.6 else 'Düşük')
    }


def get_ai_comment(material_code: str, abc_xyz: dict, pattern: str, seasonality: dict, 
                    trend: dict, intermittent: dict, forecast_rec: dict, ss_rec: dict,
                    service_level: float, risk_score: float) -> str:
    parts = []
    
    abc_label = abc_xyz['abc_label']
    xyz_label = abc_xyz['xyz_label']
    parts.append(f"📦 **{material_code}** - {abc_label} ve {xyz_label}")
    
    pattern_label = get_pattern_label(pattern)
    seasonality_text = "mevsimsellik gösteriyor" if seasonality['has_seasonality'] else "mevsimsellik göstermiyor"
    trend_text = f"{trend['trend_direction']} eğilimi var" if trend['has_trend'] else "belirgin trend yok"
    parts.append(f"📊 Talep: {pattern_label} deseninde, {seasonality_text}, {trend_text}")
    
    if intermittent['is_intermittent']:
        parts.append(f"⚠️ Aralıklı talep tespit edildi (Sıfır oranı: %{intermittent['zero_ratio']*100:.1f})")
    
    parts.append(f"🔮 Önerilen Forecast: **{forecast_rec['model_label']}** - {forecast_rec['reason']}")
    parts.append(f"📊 Önerilen SS Metodu: **{ss_rec['method_label']}** - {ss_rec['reason']}")
    parts.append(f"🎯 Önerilen Servis Seviyesi: **%{int(service_level*100)}**")
    
    if risk_score > 0.5:
        parts.append("⚠️ Risk Seviyesi: **Yüksek** - Detaylı risk yönetimi önerilir")
    elif risk_score > 0.3:
        parts.append("🟡 Risk Seviyesi: **Orta** - Düzenli takip önerilir")
    else:
        parts.append("🟢 Risk Seviyesi: **Düşük** - Mevcut strateji başarılı")
    
    if abc_xyz['abc'] == 'A' and intermittent['is_intermittent']:
        parts.append("💡 **Kritik öneri:** Yüksek maliyetli ve aralıklı talep. Stok seviyesini sıkı takip edin.")
    
    return " | ".join(parts)


def to_python_type(value):
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, np.int64, np.int32)):
        return int(value)
    if isinstance(value, (np.floating, np.float64, np.float32)):
        return float(value)
    if isinstance(value, (np.ndarray,)):
        return value.tolist()
    if isinstance(value, dict):
        return {k: to_python_type(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_python_type(v) for v in value]
    return value


def get_pattern_label(pattern: str) -> str:
    labels = {
        'DUZENLI_SABIT': 'Düzenli Sabit',
        'DUZENLI_ARTS': 'Düzenli Artan',
        'DUZENLI_AZALIS': 'Düzenli Azalan',
        'DEGISKEN': 'Değişken',
        'YUKSEK_DEGISKEN': 'Yüksek Değişken',
        'ASIRI_DEGISKEN': 'Aşırı Değişken',
        'SIFIR_TALEP': 'Sıfır Talep',
        'ARALIKLI_DUSUK': 'Aralıklı Düşük',
        'ARALIKLI_YUKSEK': 'Aralıklı Yüksek',
    }
    return labels.get(pattern, pattern)


def get_pattern_color(pattern: str) -> str:
    colors = {
        'DUZENLI_SABIT': 'success',
        'DUZENLI_ARTS': 'info',
        'DUZENLI_AZALIS': 'warning',
        'DEGISKEN': 'primary',
        'YUKSEK_DEGISKEN': 'secondary',
        'ASIRI_DEGISKEN': 'error',
        'SIFIR_TALEP': 'error',
        'ARALIKLI_DUSUK': 'info',
        'ARALIKLI_YUKSEK': 'warning',
    }
    return colors.get(pattern, 'default')


# ============================================================
# 📌 SENKRON SAFETY STOCK - AKILLI ANALİZ
# ============================================================

@router.post("/safety-stock/batch")
def calculate_safety_stock_batch(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Akıllı Emniyet Stoğu Analizi - Pattern + ABC/XYZ + Otomatik Model Seçimi
    🆕 Pricing Engine ile dinamik ücretlendirme
    """
    try:
        # 1. Cache'den verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
        
        # 2. Dataset'i al veya oluştur
        from app.services.dataset_builder import DatasetBuilder
        builder = DatasetBuilder(db)
        dataset = builder.get_dataset_by_upload_id(upload_id, current_user.id)
        
        if not dataset:
            dataset = builder.build_from_cache(
                user_id=current_user.id,
                cached_data=cached_data,
                upload_id=upload_id,
                source_type="excel",
                source_name=cached_data.get('file_name', 'unknown.xlsx')
            )
        
        # 3. Pricing Engine ile ücretlendirme
        from app.services.pricing_engine import PricingEngine
        from app.schemas.credit import PricingRequest
        
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/safety-stock/batch",
            dataset_id=dataset.id,
            user_id=current_user.id
        )
        
        pricing_response = pricing_engine.process_request(pricing_request)
        
        if not pricing_response.is_sufficient:
            raise HTTPException(
                status_code=402,
                detail=f"Yetersiz kredi! Gerekli: {pricing_response.credit_cost}, Mevcut: {pricing_response.balance_before}"
            )
        
        if not pricing_response.success:
            raise HTTPException(
                status_code=400,
                detail=pricing_response.message or "Pricing işlemi başarısız"
            )
        
        # 4. Analizi çalıştır (mevcut kod)
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        service_level = request.get('service_level', 0.95)
        
        results = []
        
        for material in materials:
            weekly_data = material.get('historical_demand', [])
            if len(weekly_data) < 4:
                continue
            
            lead_time = material.get('lead_time_days', 14)
            
            pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
            abc_xyz = calculate_abc_xyz(material, weekly_data)
            seasonality = check_seasonality(weekly_data)
            trend = check_trend(weekly_data)
            
            cv = pattern_stats.get('cv', 0)
            zero_ratio = pattern_stats.get('zero_ratio', 0)
            intermittent = check_intermittent_demand(weekly_data, zero_ratio, cv)
            
            forecast_rec = get_forecast_recommendation(seasonality, trend, intermittent, cv)
            ss_rec = get_ss_method_recommendation(pattern, pattern_stats, intermittent)
            
            ss_result = optimizer.calculate_all_methods(weekly_data, lead_time, service_level)
            
            recommended_method = ss_rec['method']
            recommended_value = ss_result.get(recommended_method, 0)
            
            risk_score = (cv * 0.4 + zero_ratio * 0.3 + (1 - service_level) * 0.3)
            risk_score = min(1.0, risk_score)
            
            ai_comment = get_ai_comment(
                material_code=material.get('code', ''),
                abc_xyz=abc_xyz,
                pattern=pattern,
                seasonality=seasonality,
                trend=trend,
                intermittent=intermittent,
                forecast_rec=forecast_rec,
                ss_rec=ss_rec,
                service_level=service_level,
                risk_score=risk_score
            )
            
            results.append({
                'material_code': str(material.get('code', '')),
                'group': str(material.get('group', 'GENEL')),
                'lead_time_days': int(lead_time),
                'pattern': str(pattern),
                'pattern_label': str(get_pattern_label(pattern)),
                'pattern_color': str(get_pattern_color(pattern)),
                'abc': str(abc_xyz['abc']),
                'abc_label': str(abc_xyz['abc_label']),
                'abc_color': str(abc_xyz['abc_color']),
                'xyz': str(abc_xyz['xyz']),
                'xyz_label': str(abc_xyz['xyz_label']),
                'xyz_color': str(abc_xyz['xyz_color']),
                'cv': float(cv),
                'zero_ratio': float(zero_ratio),
                'trend_slope': float(trend.get('trend_slope', 0)),
                'trend_direction': str(trend.get('trend_direction', 'Yok')),
                'has_seasonality': bool(seasonality['has_seasonality']),
                'seasonality_strength': float(seasonality.get('seasonality_strength', 0)),
                'seasonality_label': str(seasonality.get('seasonality_label', 'Yok')),
                'is_intermittent': bool(intermittent['is_intermittent']),
                'intermittent_level': str(intermittent['intermittent_level']),
                'forecast_model': str(forecast_rec['model']),
                'forecast_model_label': str(forecast_rec['model_label']),
                'forecast_reason': str(forecast_rec['reason']),
                'recommended_method': str(recommended_method),
                'recommended_method_label': str(ss_rec['method_label']),
                'recommended_method_reason': str(ss_rec['reason']),
                'recommended_value': float(recommended_value),
                'classic_ss': float(ss_result.get('classic_ss', 0)),
                'croston_ss': float(ss_result.get('croston_ss', 0)),
                'syntetos_boylan_ss': float(ss_result.get('syntetos_boylan_ss', 0)),
                'bootstrapping_ss': float(ss_result.get('bootstrapping_ss', 0)),
                'ml_ss': float(ss_result.get('ml_ss', 0)),
                'hybrid_ss': float(ss_result.get('hybrid_ss', 0)),
                'risk_score': float(risk_score),
                'risk_level': str('Yüksek' if risk_score > 0.5 else ('Orta' if risk_score > 0.3 else 'Düşük')),
                'ai_comment': str(ai_comment),
            })
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir sonuç üretilemedi!")
        
        # 5. Sonuçları kaydet
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'service_level': service_level,
            'pattern_analysis': True,
            'abc_xyz_analysis': True,
            'ai_analysis': True
        }
        
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='safety_stock_batch',
            data=result_data,
            params={
                'service_level': service_level,
                'total_materials': len(results),
                'pattern_analysis': True,
                'abc_xyz_analysis': True,
                'processing_score': pricing_response.processing_score,
                'credit_cost': pricing_response.credit_cost
            },
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(analysis_result)
        
        if results:
            from app.api.endpoints.learning import update_learning_from_pattern
            pattern_results = [
                {
                    'material_code': r['material_code'],
                    'group': r['group'],
                    'pattern': r['pattern'],
                    'cv': r['cv'],
                    'zero_ratio': r['zero_ratio'],
                    'trend': r['trend_direction'],
                }
                for r in results
            ]
            update_learning_from_pattern(current_user.id, pattern_results, db)
        
        db.commit()
        db.refresh(analysis_result)

        # AI Özetini arka planda oluştur
        background_tasks.add_task(
            generate_ai_summary_background,
            analysis_result.id,
            'safety_stock_batch',
            current_user.id,
            current_user.billing_country or 'TR'
        )

        # Trend Summary'yi arka planda yenile
        background_tasks.add_task(
            refresh_trend_summary,
            current_user.id,
            current_user.billing_country or 'TR'
        )

        return {
            'success': True,
            'total': len(results),
            'results': results,
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score,
            'result_id': analysis_result.id,
            'ai_status': 'pending',
            'pattern_analysis': True,
            'abc_xyz_analysis': True,
            'ai_analysis': True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# 📌 ASYNC SAFETY STOCK ANALİZİ
# ============================================================

@router.post("/safety-stock/batch/async")
def start_async_safety_stock(
    request: Dict[str, Any],  # ✅ Dict tipinde (service_level içeriyor)
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Async Emniyet Stoğu Analizi - Hemen task_id döner
    🆕 Pricing Engine ile dinamik ücretlendirme
    """
    try:
        # 1. Cache'den verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
        materials = cached_data.get('materials', [])
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        service_level = request.get('service_level', 0.95)
        
        # 2. Dataset'i al veya oluştur
        from app.services.dataset_builder import DatasetBuilder
        builder = DatasetBuilder(db)
        dataset = builder.get_dataset_by_upload_id(upload_id, current_user.id)
        
        if not dataset:
            dataset = builder.build_from_cache(
                user_id=current_user.id,
                cached_data=cached_data,
                upload_id=upload_id,
                source_type="excel",
                source_name=cached_data.get('file_name', 'unknown.xlsx')
            )
        
        # 3. Pricing Engine ile ücretlendirme (Async'de hemen düş)
        from app.services.pricing_engine import PricingEngine
        from app.schemas.credit import PricingRequest
        
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/safety-stock/batch/async",
            dataset_id=dataset.id,
            user_id=current_user.id
        )
        
        pricing_response = pricing_engine.process_request(pricing_request)
        
        if not pricing_response.is_sufficient:
            raise HTTPException(
                status_code=402,
                detail=f"Yetersiz kredi! Gerekli: {pricing_response.credit_cost}, Mevcut: {pricing_response.balance_before}"
            )
        
        if not pricing_response.success:
            raise HTTPException(
                status_code=400,
                detail=pricing_response.message or "Pricing işlemi başarısız"
            )
        
        # 4. Task ID oluştur
        task_id = str(uuid.uuid4())
        
        # 5. Initial record'u kaydet
        initial_data = {
            'status': 'processing',
            'message': 'Emniyet stoğu analizi başlatıldı, işleniyor...',
            'total': len(materials),
            'results': [],
            'service_level': service_level,
            'task_id': task_id,
            'started_at': datetime.utcnow().isoformat(),
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score
        }
        
        initial_record = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='safety_stock_batch_async',
            data=initial_data,
            params={
                'service_level': service_level,
                'total_materials': len(materials),
                'pattern_analysis': True,
                'abc_xyz_analysis': True,
                'credit_cost': pricing_response.credit_cost,
                'processing_score': pricing_response.processing_score
            },
            total_materials=len(materials),
            task_id=task_id,
            status='processing',
            progress=0,
            message='Başlatıldı...',
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(initial_record)
        db.commit()
        
        # 6. Async job'u arka planda başlat
        background_tasks.add_task(
            run_async_safety_stock_job,
            task_id=task_id,
            user_id=current_user.id,
            upload_id=upload_id,
            service_level=service_level,
            db=db
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Emniyet stoğu analizi arka planda başlatıldı.",
            "credit_cost": pricing_response.credit_cost,
            "balance_after": pricing_response.balance_after,
            "processing_score": pricing_response.processing_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# 📌 ASYNC SAFETY STOCK JOB
# ============================================================

def run_async_safety_stock_job(task_id: str, user_id: int, upload_id: str, service_level: float, db: Session):
    """Async safety stock işini gerçekleştirir."""
    try:
        logger.info(f"🔄 Async safety stock başladı: Task ID {task_id}")
        
        cached_data = get_user_upload_data(user_id)
        if not cached_data:
            update_async_task_status(db, task_id, 'failed', 'Veri bulunamadı')
            return
        
        materials = cached_data.get('materials', [])
        if not materials:
            update_async_task_status(db, task_id, 'failed', 'Malzeme bulunamadı')
            return
        
        results = []
        total = len(materials)
        
        for idx, material in enumerate(materials):
            try:
                weekly_data = material.get('historical_demand', [])
                if len(weekly_data) < 4:
                    continue
                
                lead_time = material.get('lead_time_days', 14)
                
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
                abc_xyz = calculate_abc_xyz(material, weekly_data)
                seasonality = check_seasonality(weekly_data)
                trend = check_trend(weekly_data)
                
                cv = pattern_stats.get('cv', 0)
                zero_ratio = pattern_stats.get('zero_ratio', 0)
                intermittent = check_intermittent_demand(weekly_data, zero_ratio, cv)
                
                forecast_rec = get_forecast_recommendation(seasonality, trend, intermittent, cv)
                ss_rec = get_ss_method_recommendation(pattern, pattern_stats, intermittent)
                
                ss_result = optimizer.calculate_all_methods(weekly_data, lead_time, service_level)
                
                recommended_method = ss_rec['method']
                recommended_value = ss_result.get(recommended_method, 0)
                
                risk_score = (cv * 0.4 + zero_ratio * 0.3 + (1 - service_level) * 0.3)
                risk_score = min(1.0, risk_score)
                
                ai_comment = get_ai_comment(
                    material_code=material.get('code', ''),
                    abc_xyz=abc_xyz,
                    pattern=pattern,
                    seasonality=seasonality,
                    trend=trend,
                    intermittent=intermittent,
                    forecast_rec=forecast_rec,
                    ss_rec=ss_rec,
                    service_level=service_level,
                    risk_score=risk_score
                )
                
                results.append({
                    'material_code': str(material.get('code', '')),
                    'group': str(material.get('group', 'GENEL')),
                    'lead_time_days': int(lead_time),
                    'pattern': str(pattern),
                    'pattern_label': str(get_pattern_label(pattern)),
                    'pattern_color': str(get_pattern_color(pattern)),
                    'abc': str(abc_xyz['abc']),
                    'abc_label': str(abc_xyz['abc_label']),
                    'abc_color': str(abc_xyz['abc_color']),
                    'xyz': str(abc_xyz['xyz']),
                    'xyz_label': str(abc_xyz['xyz_label']),
                    'xyz_color': str(abc_xyz['xyz_color']),
                    'cv': float(cv),
                    'zero_ratio': float(zero_ratio),
                    'trend_slope': float(trend.get('trend_slope', 0)),
                    'trend_direction': str(trend.get('trend_direction', 'Yok')),
                    'has_seasonality': bool(seasonality['has_seasonality']),
                    'seasonality_strength': float(seasonality.get('seasonality_strength', 0)),
                    'seasonality_label': str(seasonality.get('seasonality_label', 'Yok')),
                    'is_intermittent': bool(intermittent['is_intermittent']),
                    'intermittent_level': str(intermittent['intermittent_level']),
                    'forecast_model': str(forecast_rec['model']),
                    'forecast_model_label': str(forecast_rec['model_label']),
                    'forecast_reason': str(forecast_rec['reason']),
                    'recommended_method': str(recommended_method),
                    'recommended_method_label': str(ss_rec['method_label']),
                    'recommended_method_reason': str(ss_rec['reason']),
                    'recommended_value': float(recommended_value),
                    'classic_ss': float(ss_result.get('classic_ss', 0)),
                    'croston_ss': float(ss_result.get('croston_ss', 0)),
                    'syntetos_boylan_ss': float(ss_result.get('syntetos_boylan_ss', 0)),
                    'bootstrapping_ss': float(ss_result.get('bootstrapping_ss', 0)),
                    'ml_ss': float(ss_result.get('ml_ss', 0)),
                    'hybrid_ss': float(ss_result.get('hybrid_ss', 0)),
                    'risk_score': float(risk_score),
                    'risk_level': str('Yüksek' if risk_score > 0.5 else ('Orta' if risk_score > 0.3 else 'Düşük')),
                    'ai_comment': str(ai_comment),
                })
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                logger.error(f"❌ Async safety stock malzeme hatası ({material.get('code', '')}): {e}")
                continue
        
        if not results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
        # ============================================================
        # 📌 AYNI KAYDI GÜNCELLE (analysis_results)
        # ============================================================
        
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'service_level': service_level,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Emniyet stoğu analizi tamamlandı!',
            'pattern_analysis': True,
            'abc_xyz_analysis': True,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).update({
            'data': result_data,
            'status': 'completed',
            'progress': 100,
            'message': 'Tamamlandı!',
            'total_materials': len(results),
            'updated_at': datetime.utcnow()
        })
        
        # Öğrenme verilerini güncelle
        if results:
            from app.api.endpoints.learning import update_learning_from_pattern
            pattern_results = [
                {
                    'material_code': r['material_code'],
                    'group': r['group'],
                    'pattern': r['pattern'],
                    'cv': r['cv'],
                    'zero_ratio': r['zero_ratio'],
                    'trend': r['trend_direction'],
                }
                for r in results
            ]
            update_learning_from_pattern(user_id, pattern_results, db)
        
        db.commit()
        
        # ============================================================
        # 📌 BİLDİRİM OLUŞTUR
        # ============================================================
        
        try:
            notification = Notification(
                user_id=user_id,
                title=f"✅ Emniyet Stoğu Analizi Tamamlandı!",
                message=f"Emniyet stoğu raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
                type="success",
                link="/tasks"
            )
            db.add(notification)
            db.commit()
        except Exception as e:
            logger.error(f"⚠️ Bildirim hatası: {e}")
            
        # ============================================================
        # 📌 AI SUMMARY + TREND + EXECUTIVE (Hepsi Arka Planda)
        # ============================================================

        try:
            # 1. Kullanıcı bilgilerini al
            user = db.query(User).filter(User.id == user_id).first()
            country = user.billing_country if user else 'TR'
            language = get_language_from_country(country)
            
            # ✅ Sonucu al (result_data yerine doğrudan result.data kullan)
            result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
            
            if result:
                # ✅ result_type'ı result.result_type'den al
                result_type = result.result_type
                
                # 2. AI Summary oluştur
                engine = AISummaryEngine(language=language)
                summary = engine.build_summary(result_type, result.data)  # ✅ result.data kullan
                
                # 3. AnalysisResult'u güncelle
                result.ai_summary = summary
                result.ai_status = "completed"
                result.ai_version = engine.ai_version
                result.ai_created_at = datetime.utcnow()
                result.ai_prompt_version = engine.prompt_version
                result.status = 'completed'
                result.progress = 100
                result.message = 'Tamamlandı!'
                result.total_materials = len(results)
                result.updated_at = datetime.utcnow()
                result.data = result_data  # ✅ Zaten güncellenmiş data
                
                db.commit()
                logger.info(f"✅ Async AI özeti tamamlandı: {task_id}")
                
                # 4. Trend + Executive Summary yenile (Direkt çağır - arka planda)
                refresh_trend_summary(user_id, country)
                logger.info(f"✅ Async Trend/Executive Summary yenilendi: {task_id}")
                
        except Exception as e:
            logger.error(f"❌ Async AI/Trend hatası: {e}")
            db.query(AnalysisResult).filter(
                AnalysisResult.task_id == task_id
            ).update({
                'ai_status': 'failed',
                'ai_created_at': datetime.utcnow(),
            })
            db.commit()
        
        logger.info(f"✅ Async Emniyet stoku tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        logger.error(f"❌ Async safety stock hatası: {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR (Async için)
# ============================================================

def update_async_progress(db: Session, task_id: str, progress: int, message: str, completed: int):
    result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
    if result:
        data = result.data if isinstance(result.data, dict) else {}
        data['progress'] = progress
        data['message'] = message
        data['completed_materials'] = completed
        result.data = data
        db.commit()


def update_async_task_status(db: Session, task_id: str, status: str, message: str):
    db.query(AnalysisResult).filter(
        AnalysisResult.task_id == task_id
    ).update({
        'status': status,
        'message': message,
        'updated_at': datetime.utcnow()
    })
    db.commit()

# ============================================================
# 🆕 AI ÖZETİ ARKA PLANDA OLUŞTUR
# ============================================================

def generate_ai_summary_background(result_id: int, result_type: str, user_id: int, country: str = "TR"):
    """Arka planda AI özeti oluşturur"""
    try:
        from app.database import SessionLocal
        from app.models import User
        
        db2 = SessionLocal()
        try:
            user = db2.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"❌ Kullanıcı bulunamadı: {user_id}")
                return
            
            result = db2.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            if result and result.ai_summary is None:
                logger.info(f"🔄 AI özeti oluşturuluyor: {result_type} (ID: {result_id})")
                
                user_country = user.billing_country or country or "TR"
                language = get_language_from_country(user_country)
                
                engine = AISummaryEngine(language=language)
                summary = engine.build_summary(result_type, result.data)
                
                result.ai_summary = summary
                result.ai_status = "completed"
                result.ai_version = engine.ai_version
                result.ai_created_at = datetime.utcnow()
                result.ai_prompt_version = engine.prompt_version
                db2.commit()
                
                logger.info(f"✅ AI özeti tamamlandı: {result_type} (ID: {result_id}, Dil: {language})")
        finally:
            db2.close()
    except Exception as e:
        logger.error(f"❌ AI özeti oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# 📌 TREND SUMMARY YENİLEME FONKSİYONU
# ============================================================

def refresh_trend_summary(user_id: int, country: str = "TR"):
    """Trend Summary'yi yenile"""
    try:
        from app.database import SessionLocal
        from app.models import User
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"❌ Kullanıcı bulunamadı: {user_id}")
                return
            
            language = get_language_from_country(country)
            trend_engine = TrendSummaryEngine(language=language)
            exec_engine = ExecutiveSummaryEngine(language=language)
            
            # Son analizleri al
            recent_analyses = trend_engine.get_recent_analyses(db, user_id)
            if not recent_analyses:
                logger.info(f"ℹ️ Trend için yeterli analiz yok: {user_id}")
                return
            
            # Trend Summary oluştur
            trend_summary = trend_engine.build_trend_summary(recent_analyses)
            
            # Executive Summary oluştur
            executive_summary = exec_engine.build_executive_summary(
                trend_summary=trend_summary,
                previous_executive=user.executive_summary
            )
            
            # Kaydet
            user.trend_summary = trend_summary
            user.trend_updated_at = datetime.utcnow()
            user.executive_summary = executive_summary
            user.executive_updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"✅ Trend & Executive Summary yenilendi: User {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Trend yenileme hatası (User {user_id}): {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ Trend yenileme fonksiyonu hatası: {e}")

        