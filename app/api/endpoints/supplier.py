import numpy as np
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.analysis.supplier import (
    SupplierPerformanceAnalyzer, 
    SupplierShareOptimizer, 
    calculate_tail_risk_from_simulation, 
    calculate_cvar_95, 
    calculate_service_level_gap
)
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from app.api.endpoints.upload import get_user_upload_data

router = APIRouter()

# Global analyzer instance
supplier_analyzer = SupplierPerformanceAnalyzer()
share_optimizer = SupplierShareOptimizer(supplier_analyzer)


@router.post("/supplier/batch")
def analyze_suppliers_batch(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Tedarikçi Analizi - Cache'ten verileri alır.
    Token maliyeti: 5 token
    """
    try:
        # 1. Cache'ten verileri al
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        suppliers = cached_data.get('suppliers', {})
        supplier_mapping = cached_data.get('supplier_mapping', {})
        materials = cached_data.get('materials', [])
        
        # 2. Tedarikçi verisi var mı kontrol et
        if not suppliers:
            return {
                'success': False,
                'error': 'Tedarikçi verisi bulunamadı. Lütfen Excel\'e "Tedarikciler" sheet\'i ekleyin.',
                'has_suppliers': False
            }
        
        if not supplier_mapping:
            return {
                'success': False,
                'error': 'Malzeme-Tedarikçi eşleştirmesi bulunamadı. Lütfen "Malzeme_Tedarikciler" sheet\'ini ekleyin.',
                'has_suppliers': False
            }
        
        print(f"✅ {len(suppliers)} tedarikçi, {len(supplier_mapping)} eşleştirme bulundu")
        
        # 3. Tedarikçi performans analizi
        supplier_results = []
        recommendations = []
        
        for supplier_id, supplier_data in suppliers.items():
            # Tedarikçi istatistikleri
            name = supplier_data.get('name', supplier_id)
            factor = supplier_data.get('factor', 1.0)
            ontime_rate = supplier_data.get('ontime_rate', 0.8)
            lt_mean = supplier_data.get('lt_mean', 14)
            lt_std = supplier_data.get('lt_std', 3)
            
            # Risk ve performans skorları
            risk_score = 1.0 - ontime_rate
            perf_score = ontime_rate * (1.0 / factor) if factor > 0 else ontime_rate
            
            # Bu tedarikçiye bağlı malzemeler
            material_count = 0
            total_share = 0
            for mat_code, mappings in supplier_mapping.items():
                for m in mappings:
                    if m.get('supplier_id') == supplier_id:
                        material_count += 1
                        total_share += m.get('share', 0)
            
            # 📌 Detaylı tavsiye
            recommendation_parts = []
            
            if risk_score < 0.15 and perf_score > 0.85:
                recommendation_parts.append(f"✅ {name} düşük riskli ve yüksek performanslı")
                recommendation_parts.append("💡 Tercih edilmesi önerilir")
            elif risk_score > 0.4:
                recommendation_parts.append(f"🔴 {name} yüksek riskli ({risk_score*100:.0f}%)")
                recommendation_parts.append("⚠️ Alternatif tedarikçi düşünülmeli")
            elif perf_score < 0.5:
                recommendation_parts.append(f"🟡 {name} düşük performanslı ({perf_score*100:.0f}%)")
                recommendation_parts.append("📈 İyileştirme planı gerekiyor")
            else:
                recommendation_parts.append(f"🟢 {name} orta seviyede (Risk: {risk_score*100:.0f}%, Performans: {perf_score*100:.0f}%)")
                recommendation_parts.append("📊 Düzenli takip edilmeli")
            
            # Lead time bilgisi
            recommendation_parts.append(f"⏱️ Ortalama LT: {lt_mean:.0f} gün (Std: {lt_std:.0f})")
            if material_count > 0:
                recommendation_parts.append(f"📦 {material_count} malzeme bağlı, toplam pay: {total_share*100:.1f}%")
            
            recommendation = " | ".join(recommendation_parts)
            
            supplier_results.append({
                'supplier_id': supplier_id,
                'name': name,
                'risk_score': round(risk_score, 3),
                'performance_score': round(perf_score, 3),
                'ontime_rate': round(ontime_rate * 100, 1),
                'lt_mean': round(lt_mean, 1),
                'lt_std': round(lt_std, 1),
                'factor': factor,
                'material_count': material_count,
                'total_share': round(total_share, 3),
                'risk_level': 'YÜKSEK' if risk_score > 0.4 else ('ORTA' if risk_score > 0.2 else 'DÜŞÜK'),
                'performance_level': 'İYİ' if perf_score > 0.7 else ('ORTA' if perf_score > 0.4 else 'KÖTÜ'),
                'recommendation': recommendation
            })
            
            # Genel tavsiyeler
            if risk_score < 0.15 and perf_score > 0.85:
                recommendations.append(f"✅ {name}: Tercih edilen tedarikçi")
            elif risk_score > 0.4:
                recommendations.append(f"⚠️ {name}: Yüksek risk, alternatif değerlendir")
        
        # 4. Pay optimizasyonu önerisi (eğer birden fazla tedarikçi varsa)
        if len(supplier_results) > 1:
            # En iyi tedarikçiyi bul
            best_supplier = min(supplier_results, key=lambda x: x['risk_score'] * x['factor'])
            
            # Tavsiye
            share_recommendation = {
                'best_supplier': best_supplier['supplier_id'],
                'best_supplier_name': best_supplier['name'],
                'reason': f"Düşük risk ({best_supplier['risk_score']*100:.0f}%) ve yüksek performans ({best_supplier['performance_score']*100:.0f}%)"
            }
            
            # Pay dağılım önerisi
            share_advice = []
            for s in supplier_results:
                if s['supplier_id'] == best_supplier['supplier_id']:
                    share_advice.append(f"{s['name']}: %70-%80")
                elif s['risk_score'] < 0.3:
                    share_advice.append(f"{s['name']}: %15-%25")
                else:
                    share_advice.append(f"{s['name']}: %5-%10 (alternatif)")
            
            recommendations.append("📊 Pay Dağılım Önerisi: " + " | ".join(share_advice))
        
        # 5. Sonuçları kaydet
        if supplier_results:
            from app.models import UserAnalysisResult
            
            result_data = {
                'suppliers': supplier_results,
                'recommendations': recommendations,
                'total_suppliers': len(supplier_results),
                'has_suppliers': True
            }
            
            analysis_result = UserAnalysisResult(
                user_id=current_user.id,
                result_type='supplier_batch',
                material_code='ALL_SUPPLIERS',
                material_group='TEDARIKCI',
                result_data=result_data,
                params={'total_suppliers': len(supplier_results)},
                expires_at=datetime.utcnow() + timedelta(days=15)
            )
            db.add(analysis_result)
            db.commit()
        
        return {
            'success': True,
            'total_suppliers': len(supplier_results),
            'suppliers': supplier_results,
            'recommendations': recommendations,
            'has_suppliers': True,
            'token_cost': 5
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Tedarikçi analiz hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/supplier/check")
def check_supplier_data(
    current_user: User = Depends(get_current_user)
):
    """
    Tedarikçi verisi var mı kontrol et
    """
    try:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            return {
                'has_suppliers': False,
                'message': 'Henüz Excel dosyası yüklenmemiş!'
            }
        
        suppliers = cached_data.get('suppliers', {})
        supplier_mapping = cached_data.get('supplier_mapping', {})
        
        has_suppliers = bool(suppliers) and bool(supplier_mapping)
        
        return {
            'has_suppliers': has_suppliers,
            'supplier_count': len(suppliers),
            'mapping_count': len(supplier_mapping),
            'message': 'Tedarikçi verileri mevcut' if has_suppliers else 'Tedarikçi verisi bulunamadı. Excel\'e "Tedarikciler" ve "Malzeme_Tedarikciler" sheet\'leri ekleyin.'
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/supplier/{supplier_id}/risk")
def get_supplier_risk(supplier_id: str):
    """Tedarikçi risk skorunu getir"""
    try:
        risk_score = supplier_analyzer.get_supplier_risk_score(supplier_id)
        perf_score = supplier_analyzer.get_supplier_performance_score(supplier_id)
        
        return {
            "supplier_id": supplier_id,
            "risk_score": risk_score,
            "performance_score": perf_score,
            "risk_level": "YÜKSEK" if risk_score > 0.7 else ("ORTA" if risk_score > 0.4 else "DÜŞÜK"),
            "performance_level": "İYİ" if perf_score > 0.7 else ("ORTA" if perf_score > 0.4 else "KÖTÜ")
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))