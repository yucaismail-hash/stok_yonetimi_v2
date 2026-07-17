from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.safety_stock import ComprehensiveSafetyStockOptimizer
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.auth import get_current_user
from app.models import User, AnalysisResult, Notification
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import uuid
import numpy as np

router = APIRouter()
optimizer = ComprehensiveSafetyStockOptimizer()
pattern_analyzer = AdvancedDemandAnalyzer()


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
            'has_seasonality': False,  # ✅ Python bool
            'seasonal_period': 0,
            'seasonality_strength': 0,
            'seasonality_label': 'Yok'
        }
    
    first_half = demand[:len(demand)//2]
    second_half = demand[len(demand)//2:]
    if len(first_half) < 6 or len(second_half) < 6:
        return {
            'has_seasonality': False,  # ✅ Python bool
            'seasonal_period': 0,
            'seasonality_strength': 0,
            'seasonality_label': 'Yok'
        }
    
    min_len = min(len(first_half), len(second_half))
    corr = np.corrcoef(first_half[:min_len], second_half[:min_len])[0, 1] if min_len > 1 else 0
    
    # ✅ numpy.bool_ -> Python bool dönüşümü
    has_seasonality = bool(corr > 0.3)
    strength = float(round(max(0, corr), 2))  # ✅ numpy.float -> Python float
    
    return {
        'has_seasonality': has_seasonality,  # ✅ Python bool
        'seasonal_period': 12 if has_seasonality else 0,
        'seasonality_strength': strength,  # ✅ Python float
        'seasonality_label': 'Güçlü Sezonsallık' if strength > 0.6 else ('Orta Sezonsallık' if strength > 0.3 else 'Zayıf Sezonsallık')
    }

def check_trend(demand: list) -> dict:
    """Trend analizi yapar"""
    if len(demand) < 4:
        return {
            'has_trend': False,  # ✅ Python bool
            'trend_direction': 'Yok',
            'trend_strength': 0,
            'trend_slope': 0,
            'trend_label': 'Düz'
        }
    
    x = np.arange(len(demand))
    y = np.array(demand)
    
    slope, intercept = np.polyfit(x, y, 1)
    
    # ✅ numpy değerlerini Python tiplerine dönüştür
    slope = float(slope)
    trend_strength = float(round(abs(slope) / (np.mean(y) + 0.001), 3))
    has_trend = bool(abs(slope) > 0.01)  # ✅ Python bool
    
    if abs(slope) < 0.01:
        direction = 'Yok'
    elif slope > 0:
        direction = 'Artış'
    else:
        direction = 'Azalış'
    
    return {
        'has_trend': has_trend,  # ✅ Python bool
        'trend_direction': direction,
        'trend_strength': trend_strength,
        'trend_slope': slope,  # ✅ Python float
        'trend_label': f'{direction} Eğilimi' if direction != 'Yok' else 'Düz'
    }

def check_intermittent_demand(demand: list, zero_ratio: float, cv: float) -> dict:
    if not demand:
        return {'is_intermittent': False, 'intermittent_level': 'Düzenli', 'recommendation': ''}
    
    nonzero = [d for d in demand if d > 0]
    avg_nonzero = np.mean(nonzero) if nonzero else 0
    std_nonzero = np.std(nonzero) if nonzero else 0
    adi = std_nonzero / avg_nonzero if avg_nonzero > 0 else 0
    
    # ✅ Python bool
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
        'is_intermittent': is_intermittent,  # ✅ Python bool
        'intermittent_level': level,
        'zero_ratio': zero_ratio,
        'adi': float(round(adi, 2)),  # ✅ Python float
        'recommendation': recommendation
    }

def get_forecast_recommendation(seasonality: dict, trend: dict, intermittent: dict, cv: float) -> dict:
    # ✅ seasonality ve trend içindeki bool değerleri Python bool
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
    """Talep özelliklerine göre safety stock yöntemi önerir"""
    
    cv = pattern_stats.get('cv', 0)
    zero_ratio = pattern_stats.get('zero_ratio', 0)
    
    # Kural tabanı
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
    """AI yorumu oluşturur"""
    
    parts = []
    
    # 1. Ürün tanıtımı
    abc_label = abc_xyz['abc_label']
    xyz_label = abc_xyz['xyz_label']
    parts.append(f"📦 **{material_code}** - {abc_label} ve {xyz_label}")
    
    # 2. Talep yapısı
    pattern_label = get_pattern_label(pattern)
    seasonality_text = "mevsimsellik gösteriyor" if seasonality['has_seasonality'] else "mevsimsellik göstermiyor"
    trend_text = f"{trend['trend_direction']} eğilimi var" if trend['has_trend'] else "belirgin trend yok"
    parts.append(f"📊 Talep: {pattern_label} deseninde, {seasonality_text}, {trend_text}")
    
    # 3. Intermittent durumu
    if intermittent['is_intermittent']:
        parts.append(f"⚠️ Aralıklı talep tespit edildi (Sıfır oranı: %{intermittent['zero_ratio']*100:.1f})")
    
    # 4. Forecast önerisi
    parts.append(f"🔮 Önerilen Forecast: **{forecast_rec['model_label']}** - {forecast_rec['reason']}")
    
    # 5. SS önerisi
    parts.append(f"📊 Önerilen SS Metodu: **{ss_rec['method_label']}** - {ss_rec['reason']}")
    
    # 6. Servis seviyesi
    parts.append(f"🎯 Önerilen Servis Seviyesi: **%{int(service_level*100)}**")
    
    # 7. Risk değerlendirmesi
    if risk_score > 0.5:
        parts.append("⚠️ Risk Seviyesi: **Yüksek** - Detaylı risk yönetimi önerilir")
    elif risk_score > 0.3:
        parts.append("🟡 Risk Seviyesi: **Orta** - Düzenli takip önerilir")
    else:
        parts.append("🟢 Risk Seviyesi: **Düşük** - Mevcut strateji başarılı")
    
    # 8. Özel tavsiye
    if abc_xyz['abc'] == 'A' and intermittent['is_intermittent']:
        parts.append("💡 **Kritik öneri:** Yüksek maliyetli ve aralıklı talep. Stok seviyesini sıkı takip edin.")
    
    return " | ".join(parts)

def to_python_type(value):
    """Tüm numpy tiplerini Python tiplerine çevirir"""
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

# ============================================================
# 📌 SENKRON SAFETY STOCK - AKILLI ANALİZ
# ============================================================

@router.post("/safety-stock/batch")
def calculate_safety_stock_batch(
    request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Akıllı Emniyet Stoğu Analizi - Pattern + ABC/XYZ + Otomatik Model Seçimi
    Token maliyeti: 4 token
    """
    try:
        token_cost = 4
        if current_user.token_balance < token_cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Yetersiz kredi! Gerekli: {token_cost}, Mevcut: {current_user.token_balance}"
            )
        
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        upload_id = cached_data.get('upload_id')
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
            
            # ============================================================
            # 📌 1. PATTERN ANALİZİ
            # ============================================================
            pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(weekly_data)
            
            # ============================================================
            # 📌 2. ABC/XYZ ANALİZİ
            # ============================================================
            abc_xyz = calculate_abc_xyz(material, weekly_data)
            
            # ============================================================
            # 📌 3. SEZONSALLIK ANALİZİ
            # ============================================================
            seasonality = check_seasonality(weekly_data)
            
            # ============================================================
            # 📌 4. TREND ANALİZİ
            # ============================================================
            trend = check_trend(weekly_data)
            
            # ============================================================
            # 📌 5. INTERMITTENT DEMAND KONTROLÜ
            # ============================================================
            cv = pattern_stats.get('cv', 0)
            zero_ratio = pattern_stats.get('zero_ratio', 0)
            intermittent = check_intermittent_demand(weekly_data, zero_ratio, cv)
            
            # ============================================================
            # 📌 6. FORECAST MODEL ÖNERİSİ
            # ============================================================
            forecast_rec = get_forecast_recommendation(seasonality, trend, intermittent, cv)
            
            # ============================================================
            # 📌 7. SAFETY STOCK MODEL ÖNERİSİ
            # ============================================================
            ss_rec = get_ss_method_recommendation(pattern, pattern_stats, intermittent)
            
            # ============================================================
            # 📌 8. SS HESAPLAMA
            # ============================================================
            ss_result = optimizer.calculate_all_methods(weekly_data, lead_time, service_level)
            
            # Önerilen yönteme göre değeri al
            recommended_method = ss_rec['method']
            recommended_value = ss_result.get(recommended_method, 0)
            
            # ============================================================
            # 📌 9. RİSK SKORU
            # ============================================================
            risk_score = (cv * 0.4 + zero_ratio * 0.3 + (1 - service_level) * 0.3)
            risk_score = min(1.0, risk_score)
            
            # ============================================================
            # 📌 10. AI YORUMU
            # ============================================================
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
            
            # ============================================================
            # 📌 11. SONUÇ
            # ============================================================
            results.append({
                'material_code': str(material.get('code', '')),  # ✅ str
                'group': str(material.get('group', 'GENEL')),    # ✅ str
                'lead_time_days': int(lead_time),                # ✅ int
                
                # Pattern
                'pattern': str(pattern),
                'pattern_label': str(get_pattern_label(pattern)),
                'pattern_color': str(get_pattern_color(pattern)),
                
                # ABC/XYZ
                'abc': str(abc_xyz['abc']),
                'abc_label': str(abc_xyz['abc_label']),
                'abc_color': str(abc_xyz['abc_color']),
                'xyz': str(abc_xyz['xyz']),
                'xyz_label': str(abc_xyz['xyz_label']),
                'xyz_color': str(abc_xyz['xyz_color']),
                
                # Metrikler - ✅ float
                'cv': float(cv),
                'zero_ratio': float(zero_ratio),
                'trend_slope': float(trend.get('trend_slope', 0)),
                'trend_direction': str(trend.get('trend_direction', 'Yok')),
                
                # Sezonsallık
                'has_seasonality': bool(seasonality['has_seasonality']),  # ✅ bool
                'seasonality_strength': float(seasonality.get('seasonality_strength', 0)),  # ✅ float
                'seasonality_label': str(seasonality.get('seasonality_label', 'Yok')),
                
                # Intermittent
                'is_intermittent': bool(intermittent['is_intermittent']),  # ✅ bool
                'intermittent_level': str(intermittent['intermittent_level']),
                
                # Forecast
                'forecast_model': str(forecast_rec['model']),
                'forecast_model_label': str(forecast_rec['model_label']),
                'forecast_reason': str(forecast_rec['reason']),
                
                # SS
                'recommended_method': str(recommended_method),
                'recommended_method_label': str(ss_rec['method_label']),
                'recommended_method_reason': str(ss_rec['reason']),
                'recommended_value': float(recommended_value),  # ✅ float
                
                # Tüm SS değerleri - ✅ float
                'classic_ss': float(ss_result.get('classic_ss', 0)),
                'croston_ss': float(ss_result.get('croston_ss', 0)),
                'syntetos_boylan_ss': float(ss_result.get('syntetos_boylan_ss', 0)),
                'bootstrapping_ss': float(ss_result.get('bootstrapping_ss', 0)),
                'ml_ss': float(ss_result.get('ml_ss', 0)),
                'hybrid_ss': float(ss_result.get('hybrid_ss', 0)),
                
                # Risk
                'risk_score': float(risk_score),  # ✅ float
                'risk_level': str('Yüksek' if risk_score > 0.5 else ('Orta' if risk_score > 0.3 else 'Düşük')),
                
                # AI Yorumu
                'ai_comment': str(ai_comment),
            })
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir sonuç üretilemedi!")
        
        # ============================================================
        # 📌 KAYIT: analysis_results
        # ============================================================
        
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
                'abc_xyz_analysis': True
            },
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(analysis_result)
        
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
            update_learning_from_pattern(current_user.id, pattern_results, db)
        
        current_user.token_balance -= token_cost
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': token_cost,
            'new_balance': current_user.token_balance,
            'result_id': analysis_result.id,
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
# 📌 YARDIMCI FONKSİYONLAR (Aynı)
# ============================================================

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