from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.backtest import BacktestEngine
from app.auth import get_current_user
from app.models import User
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import numpy as np

router = APIRouter()
backtest_engine = BacktestEngine()


class BacktestBatchRequest(BaseModel):
    test_window: Optional[int] = 8
    strategies: Optional[List[str]] = None


@router.post("/backtest/batch")
def run_backtest_batch(
    request: BacktestBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Backtest analizi - Cache'ten verileri alır.
    Token maliyeti: 15 token
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
        
        print(f"✅ {len(materials)} malzeme bulundu")
        
        test_window = request.test_window or 8
        strategies = request.strategies
        
        all_strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        strategies_to_test = strategies if strategies else all_strategies
        
        results = []
        
        for material in materials:
            try:
                demand = material.get('historical_demand', [])
                if not demand:
                    demand = material.get('weekly_data', [])
                if not demand:
                    w_cols = [material.get(f'W{i}') for i in range(1, 20) if material.get(f'W{i}') is not None]
                    if w_cols:
                        demand = w_cols
                
                if len(demand) < 8:
                    print(f"⚠️ {material.get('code', 'Bilinmeyen')}: {len(demand)} hafta veri (8+ gerekli)")
                    continue
                
                print(f"✅ {material.get('code', 'Bilinmeyen')}: {len(demand)} hafta veri ile backtest başlıyor...")
                
                backtest_result = backtest_engine.run_backtest(
                    historical_demand=demand,
                    lead_time_days=material.get('lead_time_days', 14),
                    holding_cost_rate=0.20,
                    shortage_cost=500,
                    unit_cost=100,
                    test_window=test_window,
                    strategies=strategies_to_test
                )
                
                if 'error' in backtest_result:
                    print(f"⚠️ {material.get('code')}: {backtest_result['error']}")
                    continue
                
                comparison = backtest_result.get('comparison', {})
                
                # 📌 Tüm metrikleri al
                service_levels = comparison.get('service_level', {})
                total_costs = comparison.get('total_cost', {})
                holding_costs = comparison.get('total_holding_cost', {})
                shortage_costs = comparison.get('total_shortage_cost', {})
                stockout_probs = comparison.get('stockout_probability', {})
                total_shortages = comparison.get('total_shortage', {})
                
                best_strategy = backtest_result.get('recommendation', {}).get('best_strategy', 'hybrid')
                
                # Her stratejinin detaylarını topla
                strategy_details = {}
                for strat in strategies_to_test:
                    strategy_details[strat] = {
                        'service_level': service_levels.get(strat, 0),
                        'total_cost': total_costs.get(strat, 0),
                        'holding_cost': holding_costs.get(strat, 0) if holding_costs else 0,
                        'shortage_cost': shortage_costs.get(strat, 0) if shortage_costs else 0,
                        'stockout_probability': stockout_probs.get(strat, 0) if stockout_probs else 0,
                        'total_shortage': total_shortages.get(strat, 0) if total_shortages else 0
                    }
                
                # 📌 En iyi strateji için metrikler
                service_level = service_levels.get(best_strategy, 0)
                total_cost = total_costs.get(best_strategy, 0)
                stockout_prob = stockout_probs.get(best_strategy, 0) if stockout_probs else 0
                total_shortage = total_shortages.get(best_strategy, 0) if total_shortages else 0
                
                # 📌 Tail Risk hesapla
                tail_risk = min(1.0, stockout_prob * 2.5)
                if tail_risk > 0.6:
                    tail_risk_level = "🔴 Yüksek"
                elif tail_risk > 0.3:
                    tail_risk_level = "🟡 Orta"
                else:
                    tail_risk_level = "🟢 Düşük"
                
                # 📌 Detaylı tavsiye
                avg_demand = np.mean(demand) if demand else 0
                lead_time = material.get('lead_time_days', 14)
                current_rop = int(avg_demand * (lead_time / 7))
                
                recommendation_parts = []
                rop_increase = 0
                recommended_rop = current_rop
                
                if service_level < 0.85:
                    gap = (0.95 - service_level) * 100
                    ss_increase = int((gap / 100) * avg_demand * (lead_time / 7))
                    rop_increase = ss_increase
                    recommended_rop = current_rop + rop_increase
                    new_ss = int((service_level + (gap / 100)) * avg_demand * (lead_time / 7))
                    current_ss = int(service_level * avg_demand * (lead_time / 7))
                    
                    recommendation_parts.append(f"🔴 Servis seviyesi %{service_level*100:.1f} (hedef %95, {gap:.1f} puan eksi)")
                    recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                    recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                    recommendation_parts.append(f"💡 Önerilen strateji: {best_strategy}")
                    if tail_risk > 0.5:
                        recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                    
                elif service_level < 0.95:
                    gap = (0.95 - service_level) * 100
                    ss_increase = int((gap / 100) * avg_demand * (lead_time / 7) * 0.5)
                    rop_increase = ss_increase
                    recommended_rop = current_rop + rop_increase
                    new_ss = int((service_level + (gap / 100) * 0.5) * avg_demand * (lead_time / 7))
                    current_ss = int(service_level * avg_demand * (lead_time / 7))
                    
                    recommendation_parts.append(f"🟡 Servis seviyesi %{service_level*100:.1f} (hedef %95, {gap:.1f} puan eksi)")
                    recommendation_parts.append(f"📈 ROP'u {rop_increase} birim artırın (mevcut: {current_rop} → {recommended_rop})")
                    recommendation_parts.append(f"📊 SS'yi {current_ss} → {new_ss} birim artırın")
                    recommendation_parts.append(f"💡 Mevcut strateji: {best_strategy}")
                    if tail_risk > 0.5:
                        recommendation_parts.append("⚠️ Tail Risk yüksek, ek SS önerilir")
                    
                else:
                    recommendation_parts.append(f"✅ Servis seviyesi %{service_level*100:.1f} (hedef %95, başarılı)")
                    recommendation_parts.append(f"💡 Mevcut strateji: {best_strategy} başarılı")
                
                recommendation = " | ".join(recommendation_parts)
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'best_strategy': best_strategy,
                    'service_level': service_level,
                    'total_cost': total_cost,
                    'holding_cost': holding_costs.get(best_strategy, 0) if holding_costs else 0,
                    'shortage_cost': shortage_costs.get(best_strategy, 0) if shortage_costs else 0,
                    'stockout_probability': round(stockout_prob * 100, 1),
                    'tail_risk': round(tail_risk, 3),
                    'tail_risk_level': tail_risk_level,
                    'total_shortage': round(total_shortage, 2),
                    'strategies_tested': len(strategies_to_test),
                    'strategy_details': strategy_details,
                    'recommendation': recommendation,
                    'current_rop': current_rop,
                    'recommended_rop': recommended_rop
                })
                
                print(f"✅ {material.get('code')}: En iyi = {best_strategy}, Servis = {service_level:.2f}, Tail Risk = {tail_risk:.2f}")
                
            except Exception as e:
                print(f"❌ Backtest hatası ({material.get('code', 'Bilinmeyen')}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if results:
            from app.models import UserAnalysisResult
            
            for result in results:
                result_data = result.copy()
                result_data['strategy_details'] = result.get('strategy_details', {})
                
                analysis_result = UserAnalysisResult(
                    user_id=current_user.id,
                    result_type='backtest_batch',
                    material_code=result['material_code'],
                    material_group=result.get('group', 'GENEL'),
                    result_data=result_data,
                    params={
                        'test_window': test_window,
                        'strategies_tested': result['strategies_tested'],
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
            'token_cost': 15
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Backtest genel hata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))