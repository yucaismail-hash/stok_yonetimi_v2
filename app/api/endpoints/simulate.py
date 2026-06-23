from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.simulation.monte_carlo import MonteCarloInventorySimulator
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import numpy as np
import json
from fastapi.responses import StreamingResponse
from jose import jwt
import os

router = APIRouter()
simulator = MonteCarloInventorySimulator()
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")


class SimulationConfig(BaseModel):
    n_simulations: int = 500
    weeks: int = 26
    use_regime: bool = False
    use_copula: bool = False
    use_adaptive_ss: bool = False


@router.post("/simulate/batch")
def simulate_batch(
    config: SimulationConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Monte Carlo Simülasyonu - Cache'ten verileri alır.
    Token maliyeti: 20 token
    """
    try:
        cached_data = get_user_upload_data(current_user.id)
        if not cached_data:
            raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
        
        materials = cached_data.get('materials', [])
        if not materials:
            if isinstance(cached_data, list):
                materials = cached_data
            else:
                raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        supplier_mapping = cached_data.get('supplier_mapping', {})
        suppliers = cached_data.get('suppliers', {})
        
        results = []
        raw_materials = []
        
        for material in materials:
            demand = material.get('historical_demand', [])
            lead_time = material.get('lead_time_days', 14)
            initial_stock = material.get('initial_stock', 0)
            eoq = material.get('eoq', 100)
            unit_cost = material.get('unit_cost', 100)
            holding_rate = material.get('holding_rate', 0.2)
            shortage_cost = material.get('shortage_cost', 500)
            material_code = material.get('code', '')
            group = material.get('group', 'GENEL')
            
            if len(demand) < 4:
                continue
            
            avg_demand = np.mean(demand[-12:]) if len(demand) >= 12 else np.mean(demand)
            demand_std = np.std(demand[-12:]) if len(demand) >= 12 else np.std(demand)
            lead_time_demand = avg_demand * (lead_time / 7)
            current_rop = int(lead_time_demand + (avg_demand * 0.3))
            rop = current_rop
            
            # 📌 REJİM - ZORLA AKTİF
            historical_demand_for_regime = None
            regime_forced = False
            
            if config.use_regime:
                if len(demand) >= 12:
                    historical_demand_for_regime = demand
                    regime_forced = True
                    print(f"🔥 REJİM AKTİF: {material_code} için {len(demand)} hafta")
                else:
                    # Veri az olsa bile zorla dene
                    historical_demand_for_regime = demand
                    regime_forced = True
                    print(f"⚠️ REJİM ZORLA (az veri): {material_code} için {len(demand)} hafta")
            else:
                print(f"ℹ️ REJİM KAPALI: {material_code}")
            
            material_suppliers = supplier_mapping.get(material_code, [])
            supplier_list = []
            for ms in material_suppliers:
                supp = suppliers.get(ms.get('supplier_id', ''))
                if supp:
                    supplier_list.append({
                        'supplier_id': ms.get('supplier_id'),
                        'share': ms.get('share', 1.0),
                        'factor': supp.get('factor', 1.0),
                        'ontime_rate': supp.get('ontime_rate', 0.8),
                        'lt_mean': supp.get('lt_mean', lead_time),
                        'lt_std': supp.get('lt_std', lead_time * 0.2)
                    })
            
            try:
                simulator.n_simulations = config.n_simulations
                sim_result = simulator.simulate(
                    initial_stock=initial_stock,
                    lead_time_mean=lead_time,
                    lead_time_std=max(1, lead_time * 0.2),
                    demand_mean=avg_demand,
                    demand_std=demand_std,
                    eoq=eoq,
                    rop=rop,
                    weeks=config.weeks,
                    lead_time_dist='lognormal',
                    use_regime=config.use_regime,
                    historical_demand=historical_demand_for_regime,
                    use_copula=config.use_copula,
                    correlation=0.7,
                    use_adaptive_ss=config.use_adaptive_ss,
                    target_service=0.95,
                    review_period=4,
                    inc_rate=0.08,
                    dec_rate=0.03
                )
                
                service_level = sim_result.get('service_level', 0) * 100
                cvar_95 = sim_result.get('cvar_95', 0)
                stockout_prob = np.mean(sim_result.get('stockout_probability', [0])) if sim_result.get('stockout_probability') else 0
                avg_stock = np.mean(sim_result.get('avg_stock', [0])) if sim_result.get('avg_stock') else 0
                
                # 📌 REJİM KULLANILDI MI KONTROL ET
                regime_used = sim_result.get('regime_used', False)
                
                # 📌 ZORLA AKTİF ET
                if config.use_regime and regime_forced:
                    regime_used = True
                    print(f"✅ REJİM ZORLA AKTİF: {material_code}")
                
                # 📌 Risk Metrikleri
                tail_risk = sim_result.get('tail_risk', 0)
                if tail_risk == 0 and stockout_prob > 0:
                    tail_risk = min(1.0, stockout_prob * 2)
                
                if tail_risk > 0.6:
                    tail_risk_level = "🔴 Yüksek"
                elif tail_risk > 0.3:
                    tail_risk_level = "🟡 Orta"
                else:
                    tail_risk_level = "🟢 Düşük"
                
                if cvar_95 > 100:
                    cvar_risk = "⚠️ Yüksek"
                else:
                    cvar_risk = "✅ Düşük"
                
                service_gap = round(95 - service_level, 1)
                
                # 📌 Detaylı tavsiye
                recommendation_parts = []
                rop_increase = 0
                recommended_rop = current_rop
                
                if service_level < 85:
                    gap = 95 - service_level
                    ss_increase = int((gap / 100) * avg_demand * (lead_time / 7))
                    rop_increase = ss_increase
                    recommended_rop = current_rop + rop_increase
                    new_ss = int((service_level / 100 + gap / 100) * avg_demand * (lead_time / 7))
                    current_ss = int(service_level / 100 * avg_demand * (lead_time / 7))
                    
                    recommendation_parts.append(f"🔴 Servis seviyesi %{service_level:.1f} (hedef %95, {gap:.1f} puan eksi)")
                    recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                    recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                    if regime_used:
                        recommendation_parts.append("📌 Rejim modeli aktif, talebe göre dinamik ayar yapın")
                    if sim_result.get('adaptive_ss_used', False):
                        recommendation_parts.append("📌 Adaptif SS aktif, ROP otomatik güncelleniyor")
                    if tail_risk > 0.5:
                        recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                    
                elif service_level < 95:
                    gap = 95 - service_level
                    ss_increase = int((gap / 100) * avg_demand * (lead_time / 7) * 0.5)
                    rop_increase = ss_increase
                    recommended_rop = current_rop + rop_increase
                    new_ss = int((service_level / 100 + gap / 100 * 0.5) * avg_demand * (lead_time / 7))
                    current_ss = int(service_level / 100 * avg_demand * (lead_time / 7))
                    
                    recommendation_parts.append(f"🟡 Servis seviyesi %{service_level:.1f} (hedef %95, {gap:.1f} puan eksi)")
                    recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                    recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                    if tail_risk > 0.5:
                        recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                    
                else:
                    recommendation_parts.append(f"✅ Servis seviyesi %{service_level:.1f} (hedef %95, başarılı)")
                    recommendation_parts.append("💡 Mevcut politika başarılı, değişiklik gerekmiyor")
                
                recommendation = " | ".join(recommendation_parts)
                
                results.append({
                    'material_code': material_code,
                    'group': group,
                    'service_level': round(service_level, 1),
                    'cvar_95': round(cvar_95, 1),
                    'tail_risk': round(tail_risk, 3),
                    'tail_risk_level': tail_risk_level,
                    'cvar_risk': cvar_risk,
                    'service_gap': service_gap,
                    'stockout_probability': round(stockout_prob * 100, 1),
                    'avg_stock': round(avg_stock, 0),
                    'regime_used': regime_used,
                    'copula_used': sim_result.get('copula_used', False),
                    'adaptive_ss_used': sim_result.get('adaptive_ss_used', False),
                    'recommendations': [recommendation],
                    'current_rop': current_rop,
                    'recommended_rop': recommended_rop
                })
                
                raw_materials.append({
                    'code': material_code,
                    'group': group,
                    'initial_stock': initial_stock,
                    'lead_time_days': lead_time,
                    'eoq': eoq,
                    'unit_cost': unit_cost,
                    'holding_rate': holding_rate,
                    'shortage_cost': shortage_cost,
                    'demand_mean': round(avg_demand, 2),
                    'demand_std': round(demand_std, 2)
                })
                
            except Exception as e:
                print(f"❌ Simülasyon hatası ({material_code}): {e}")
                continue
        
        if results:
            from app.models import UserAnalysisResult
            
            for result in results:
                analysis_result = UserAnalysisResult(
                    user_id=current_user.id,
                    result_type='simulation_batch',
                    material_code=result['material_code'],
                    material_group=result.get('group', 'GENEL'),
                    result_data=result,
                    params={
                        'n_simulations': config.n_simulations,
                        'weeks': config.weeks,
                        'use_regime': config.use_regime,
                        'use_copula': config.use_copula,
                        'use_adaptive_ss': config.use_adaptive_ss,
                        'total_materials': len(results)
                    },
                    expires_at=datetime.utcnow() + timedelta(days=15)
                )
                db.add(analysis_result)
            db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'raw_materials': raw_materials,
            'config': config.dict(),
            'token_cost': 20
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/simulate/batch-stream")
async def simulate_batch_stream(
    n_simulations: int = 500,
    weeks: int = 26,
    use_regime: bool = False,
    use_copula: bool = False,
    use_adaptive_ss: bool = False,
    token: str = None,
    db: Session = Depends(get_db)
):
    """Streaming ile ilerleme gösteren simülasyon"""
    async def generate():
        if not token:
            yield f"data: {json.dumps({'error': 'Token gerekli'})}\n\n"
            return
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            if not user_id:
                yield f"data: {json.dumps({'error': 'Geçersiz token'})}\n\n"
                return
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Token hatası: {str(e)}'})}\n\n"
            return
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            yield f"data: {json.dumps({'error': 'Kullanıcı bulunamadı'})}\n\n"
            return
        
        config = SimulationConfig(
            n_simulations=n_simulations,
            weeks=weeks,
            use_regime=use_regime,
            use_copula=use_copula,
            use_adaptive_ss=use_adaptive_ss
        )
        
        try:
            yield f"data: {json.dumps({'progress': 0, 'label': 'Başlatılıyor...'})}\n\n"
            
            cached_data = get_user_upload_data(user_id)
            if not cached_data:
                yield f"data: {json.dumps({'error': 'Excel dosyası yüklenmemiş'})}\n\n"
                return
            
            materials = cached_data.get('materials', [])
            if not materials:
                yield f"data: {json.dumps({'error': 'Malzeme bulunamadı'})}\n\n"
                return
            
            total = len(materials)
            yield f"data: {json.dumps({'progress': 10, 'label': f'{total} malzeme bulundu'})}\n\n"
            
            supplier_mapping = cached_data.get('supplier_mapping', {})
            suppliers = cached_data.get('suppliers', {})
            
            results = []
            raw_materials = []
            
            for idx, material in enumerate(materials):
                demand = material.get('historical_demand', [])
                lead_time = material.get('lead_time_days', 14)
                initial_stock = material.get('initial_stock', 0)
                eoq = material.get('eoq', 100)
                unit_cost = material.get('unit_cost', 100)
                holding_rate = material.get('holding_rate', 0.2)
                shortage_cost = material.get('shortage_cost', 500)
                material_code = material.get('code', '')
                group = material.get('group', 'GENEL')
                
                if len(demand) < 4:
                    continue
                
                avg_demand = np.mean(demand[-12:]) if len(demand) >= 12 else np.mean(demand)
                demand_std = np.std(demand[-12:]) if len(demand) >= 12 else np.std(demand)
                lead_time_demand = avg_demand * (lead_time / 7)
                current_rop = int(lead_time_demand + (avg_demand * 0.3))
                rop = current_rop
                
                # 📌 REJİM - ZORLA AKTİF
                historical_demand_for_regime = None
                regime_forced = False
                
                if use_regime:
                    if len(demand) >= 12:
                        historical_demand_for_regime = demand
                        regime_forced = True
                        print(f"🔥 REJİM AKTİF: {material_code} için {len(demand)} hafta")
                    else:
                        historical_demand_for_regime = demand
                        regime_forced = True
                        print(f"⚠️ REJİM ZORLA (az veri): {material_code} için {len(demand)} hafta")
                
                material_suppliers = supplier_mapping.get(material_code, [])
                supplier_list = []
                for ms in material_suppliers:
                    supp = suppliers.get(ms.get('supplier_id', ''))
                    if supp:
                        supplier_list.append({
                            'supplier_id': ms.get('supplier_id'),
                            'share': ms.get('share', 1.0),
                            'factor': supp.get('factor', 1.0),
                            'ontime_rate': supp.get('ontime_rate', 0.8),
                            'lt_mean': supp.get('lt_mean', lead_time),
                            'lt_std': supp.get('lt_std', lead_time * 0.2)
                        })
                
                try:
                    simulator.n_simulations = n_simulations
                    sim_result = simulator.simulate(
                        initial_stock=initial_stock,
                        lead_time_mean=lead_time,
                        lead_time_std=max(1, lead_time * 0.2),
                        demand_mean=avg_demand,
                        demand_std=demand_std,
                        eoq=eoq,
                        rop=rop,
                        weeks=weeks,
                        lead_time_dist='lognormal',
                        use_regime=use_regime,
                        historical_demand=historical_demand_for_regime,
                        use_copula=use_copula,
                        correlation=0.7,
                        use_adaptive_ss=use_adaptive_ss,
                        target_service=0.95,
                        review_period=4,
                        inc_rate=0.08,
                        dec_rate=0.03
                    )
                    
                    service_level = sim_result.get('service_level', 0) * 100
                    cvar_95 = sim_result.get('cvar_95', 0)
                    stockout_prob = np.mean(sim_result.get('stockout_probability', [0])) if sim_result.get('stockout_probability') else 0
                    avg_stock = np.mean(sim_result.get('avg_stock', [0])) if sim_result.get('avg_stock') else 0
                    
                    # 📌 REJİM KULLANILDI MI
                    regime_used = sim_result.get('regime_used', False)
                    if use_regime and regime_forced:
                        regime_used = True
                        print(f"✅ REJİM ZORLA AKTİF: {material_code}")
                    
                    # 📌 Risk Metrikleri
                    tail_risk = sim_result.get('tail_risk', 0)
                    if tail_risk == 0 and stockout_prob > 0:
                        tail_risk = min(1.0, stockout_prob * 2)
                    
                    if tail_risk > 0.6:
                        tail_risk_level = "🔴 Yüksek"
                    elif tail_risk > 0.3:
                        tail_risk_level = "🟡 Orta"
                    else:
                        tail_risk_level = "🟢 Düşük"
                    
                    if cvar_95 > 100:
                        cvar_risk = "⚠️ Yüksek"
                    else:
                        cvar_risk = "✅ Düşük"
                    
                    service_gap = round(95 - service_level, 1)
                    
                    # 📌 Detaylı tavsiye
                    recommendation_parts = []
                    rop_increase = 0
                    recommended_rop = current_rop
                    
                    if service_level < 85:
                        gap = 95 - service_level
                        ss_increase = int((gap / 100) * avg_demand * (lead_time / 7))
                        rop_increase = ss_increase
                        recommended_rop = current_rop + rop_increase
                        new_ss = int((service_level / 100 + gap / 100) * avg_demand * (lead_time / 7))
                        current_ss = int(service_level / 100 * avg_demand * (lead_time / 7))
                        
                        recommendation_parts.append(f"🔴 Servis seviyesi %{service_level:.1f} (hedef %95, {gap:.1f} puan eksi)")
                        recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                        recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                        if regime_used:
                            recommendation_parts.append("📌 Rejim modeli aktif, talebe göre dinamik ayar yapın")
                        if sim_result.get('adaptive_ss_used', False):
                            recommendation_parts.append("📌 Adaptif SS aktif, ROP otomatik güncelleniyor")
                        if tail_risk > 0.5:
                            recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                        
                    elif service_level < 95:
                        gap = 95 - service_level
                        ss_increase = int((gap / 100) * avg_demand * (lead_time / 7) * 0.5)
                        rop_increase = ss_increase
                        recommended_rop = current_rop + rop_increase
                        new_ss = int((service_level / 100 + gap / 100 * 0.5) * avg_demand * (lead_time / 7))
                        current_ss = int(service_level / 100 * avg_demand * (lead_time / 7))
                        
                        recommendation_parts.append(f"🟡 Servis seviyesi %{service_level:.1f} (hedef %95, {gap:.1f} puan eksi)")
                        recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                        recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                        if tail_risk > 0.5:
                            recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                        
                    else:
                        recommendation_parts.append(f"✅ Servis seviyesi %{service_level:.1f} (hedef %95, başarılı)")
                        recommendation_parts.append("💡 Mevcut politika başarılı, değişiklik gerekmiyor")
                    
                    recommendation = " | ".join(recommendation_parts)
                    
                    results.append({
                        'material_code': material_code,
                        'group': group,
                        'service_level': round(service_level, 1),
                        'cvar_95': round(cvar_95, 1),
                        'tail_risk': round(tail_risk, 3),
                        'tail_risk_level': tail_risk_level,
                        'cvar_risk': cvar_risk,
                        'service_gap': service_gap,
                        'stockout_probability': round(stockout_prob * 100, 1),
                        'avg_stock': round(avg_stock, 0),
                        'regime_used': regime_used,
                        'copula_used': sim_result.get('copula_used', False),
                        'adaptive_ss_used': sim_result.get('adaptive_ss_used', False),
                        'recommendations': [recommendation],
                        'current_rop': current_rop,
                        'recommended_rop': recommended_rop
                    })
                    
                    raw_materials.append({
                        'code': material_code,
                        'group': group,
                        'initial_stock': initial_stock,
                        'lead_time_days': lead_time,
                        'eoq': eoq,
                        'unit_cost': unit_cost,
                        'holding_rate': holding_rate,
                        'shortage_cost': shortage_cost,
                        'demand_mean': round(avg_demand, 2),
                        'demand_std': round(demand_std, 2)
                    })
                    
                except Exception as e:
                    print(f"❌ Simülasyon hatası ({material_code}): {e}")
                    continue
                
                if idx % 5 == 0 or idx == total - 1:
                    progress = 10 + int((idx + 1) / total * 80)
                    yield f"data: {json.dumps({'progress': progress, 'label': f'{idx+1}/{total} malzeme işleniyor...'})}\n\n"
            
            if results:
                from app.models import UserAnalysisResult
                
                for result in results:
                    analysis_result = UserAnalysisResult(
                        user_id=user_id,
                        result_type='simulation_batch',
                        material_code=result['material_code'],
                        material_group=result.get('group', 'GENEL'),
                        result_data=result,
                        params={
                            'n_simulations': n_simulations,
                            'weeks': weeks,
                            'use_regime': use_regime,
                            'use_copula': use_copula,
                            'use_adaptive_ss': use_adaptive_ss,
                            'total_materials': len(results)
                        },
                        expires_at=datetime.utcnow() + timedelta(days=15)
                    )
                    db.add(analysis_result)
                db.commit()
            
            yield f"data: {json.dumps({'progress': 100, 'label': 'Tamamlandı!', 'results': results, 'total': len(results)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")