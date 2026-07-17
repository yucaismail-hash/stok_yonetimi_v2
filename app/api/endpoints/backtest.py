from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.backtest import BacktestEngine
from app.auth import get_current_user
from app.models import User, AnalysisResult, Notification
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.api.endpoints.upload import get_user_upload_data
import numpy as np
import uuid

router = APIRouter()
backtest_engine = BacktestEngine()


class BacktestBatchRequest(BaseModel):
    test_window: Optional[int] = 8
    strategies: Optional[List[str]] = None


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
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

# backtest.py - DOĞRU VALIDASYON

def validate_backtest_data(materials: list, test_window: int) -> tuple:
    """
    Backtest için verileri validate eder.
    Literatür: En az 8 hafta veri gereklidir.
    test_window + 4 hafta buffer (en az 8 hafta)
    """
    if not materials:
        return False, "Hiç malzeme verisi bulunamadı!", 0, 0
    
    # En uzun historical_demand'i bul
    max_weeks = 0
    for material in materials:
        demand = material.get('historical_demand', [])
        if not demand:
            demand = material.get('weekly_data', [])
        if not demand:
            w_cols = [material.get(f'W{i}') for i in range(1, 20) if material.get(f'W{i}') is not None]
            if w_cols:
                demand = w_cols
        if len(demand) > max_weeks:
            max_weeks = len(demand)
    
    # ✅ LİTERATÜR: Minimum 8 hafta (test_window + 4 buffer)
    min_required = max(8, test_window + 4)
    
    if max_weeks < min_required:
        return False, f"Yetersiz veri! Yüklenen en uzun veri {max_weeks} hafta, backtest için en az {min_required} hafta gerekiyor.", min_required, max_weeks
    
    return True, f"Veri yeterli ({max_weeks} hafta)", min_required, max_weeks

# ============================================================
# 📌 SENKRON BACKTEST
# ============================================================

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
        
        upload_id = cached_data.get('upload_id')
        
        # ✅ DOĞRU materials kontrolü
        materials = cached_data.get('materials', [])
        
        # ❌ YANLIŞ: Eğer cached_data bir liste ise, materials olarak kullan
        # Bu kısım YANLIŞ çünkü cached_data her zaman dict dönüyor!
        # if not materials:
        #     if isinstance(cached_data, list):
        #         materials = cached_data
        
        if not materials:
            raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
        
        print(f"✅ {len(materials)} malzeme bulundu")
        
        test_window = request.test_window or 8
        strategies = request.strategies
        
        all_strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        strategies_to_test = strategies if strategies else all_strategies
        
        results = []
        
        for material in materials:
            try:
                # ✅ historical_demand kontrolü
                demand = material.get('historical_demand', [])
                if not demand:
                    demand = material.get('weekly_data', [])
                if not demand:
                    # Excel'de W1, W2... formatında olabilir
                    w_cols = [material.get(f'W{i}') for i in range(1, 20) if material.get(f'W{i}') is not None]
                    if w_cols:
                        demand = w_cols
                
                # ✅ En az 8 hafta veri kontrolü
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
                
                service_levels = comparison.get('service_level', {})
                total_costs = comparison.get('total_cost', {})
                holding_costs = comparison.get('total_holding_cost', {})
                shortage_costs = comparison.get('total_shortage_cost', {})
                stockout_probs = comparison.get('stockout_probability', {})
                total_shortages = comparison.get('total_shortage', {})
                
                best_strategy = backtest_result.get('recommendation', {}).get('best_strategy', 'hybrid')
                
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
                
                service_level = service_levels.get(best_strategy, 0)
                total_cost = total_costs.get(best_strategy, 0)
                stockout_prob = stockout_probs.get(best_strategy, 0) if stockout_probs else 0
                total_shortage = total_shortages.get(best_strategy, 0) if total_shortages else 0
                
                tail_risk = min(1.0, stockout_prob * 2.5)
                if tail_risk > 0.6:
                    tail_risk_level = "🔴 Yüksek"
                elif tail_risk > 0.3:
                    tail_risk_level = "🟡 Orta"
                else:
                    tail_risk_level = "🟢 Düşük"
                
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
                    'recommended_rop': recommended_rop,
                    'pattern': 'DEGISKEN',
                    'cv': round(np.std(demand) / np.mean(demand) if np.mean(demand) > 0 else 0, 4)
                })
                
                print(f"✅ {material.get('code')}: En iyi = {best_strategy}, Servis = {service_level:.2f}, Tail Risk = {tail_risk:.2f}")
                
            except Exception as e:
                print(f"❌ Backtest hatası ({material.get('code', 'Bilinmeyen')}): {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir sonuç üretilemedi! Lütfen verilerinizi kontrol edin.")
        
        # ============================================================
        # 📌 TEK KAYIT: analysis_results (Senkron - task_id NULL)
        # ============================================================
        
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'test_window': test_window,
            'strategies_tested': strategies_to_test
        }
        
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='backtest_batch',
            data=result_data,
            params={
                'test_window': test_window,
                'strategies_tested': len(strategies_to_test),
                'total_materials': len(results)
            },
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        db.add(analysis_result)
        db.commit()
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'token_cost': 15,
            'result_id': analysis_result.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"❌ Backtest genel hata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))
    
# ============================================================
# 📌 ASYNC BACKTEST
# ============================================================

@router.post("/backtest/batch/async")
def start_async_backtest(
    request: BacktestBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Async backtest başlatır. Hemen task_id döner."""
    
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş!")
    
    upload_id = cached_data.get('upload_id')
    materials = cached_data.get('materials', [])
    if not materials:
        raise HTTPException(status_code=404, detail="Yüklenen veride malzeme bulunamadı!")
    
    print(f"✅ Async backtest başlatılıyor: {len(materials)} malzeme")
    
    task_id = str(uuid.uuid4())
    
    test_window = request.test_window or 8
    strategies = request.strategies
    
    all_strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 'ml', 'hybrid', 'simple_moving_avg', 'last_value']
    strategies_to_test = strategies if strategies else all_strategies
    
    # ============================================================
    # 📌 TEK KAYIT: analysis_results (Async - task_id dolu)
    # ============================================================
    
    initial_data = {
        'status': 'processing',
        'message': 'Backtest başlatıldı, işleniyor...',
        'total': len(materials),
        'results': [],
        'test_window': test_window,
        'strategies': strategies,
        'task_id': task_id,
        'started_at': datetime.utcnow().isoformat()
    }
    
    initial_record = AnalysisResult(
        user_id=current_user.id,
        upload_id=upload_id,
        result_type='backtest_batch_async',
        data=initial_data,
        params={
            'test_window': test_window,
            'strategies_tested': len(strategies_to_test),
            'total_materials': len(materials)
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
    
    background_tasks.add_task(
        run_async_backtest_job,
        task_id=task_id,
        user_id=current_user.id,
        upload_id=upload_id,
        request=request,
        db=db
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": "Backtest arka planda başlatıldı.",
        "token_cost": 15
    }


def run_async_backtest_job(task_id: str, user_id: int, upload_id: str, request: BacktestBatchRequest, db: Session):
    """Async backtest işini gerçekleştirir."""
    try:
        print(f"🔄 Async backtest başladı: Task ID {task_id}")
        
        cached_data = get_user_upload_data(user_id)
        if not cached_data:
            update_async_task_status(db, task_id, 'failed', 'Veri bulunamadı')
            return
        
        materials = cached_data.get('materials', [])
        if not materials:
            update_async_task_status(db, task_id, 'failed', 'Malzeme bulunamadı')
            return
        
        print(f"✅ {len(materials)} malzeme ile async backtest başlıyor...")
        
        test_window = request.test_window or 8
        strategies = request.strategies
        all_strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        strategies_to_test = strategies if strategies else all_strategies
        
        results = []
        total = len(materials)
        
        for idx, material in enumerate(materials):
            try:
                demand = material.get('historical_demand', [])
                if not demand:
                    demand = material.get('weekly_data', [])
                if not demand:
                    w_cols = [material.get(f'W{i}') for i in range(1, 20) if material.get(f'W{i}') is not None]
                    if w_cols:
                        demand = w_cols
                
                if len(demand) < 8:
                    print(f"⚠️ Async: {material.get('code', 'Bilinmeyen')}: {len(demand)} hafta veri (8+ gerekli) - atlanıyor")
                    continue
                
                print(f"✅ Async: {material.get('code', 'Bilinmeyen')}: {len(demand)} hafta veri ile backtest başlıyor...")
                
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
                    print(f"⚠️ Async: {material.get('code')}: {backtest_result['error']}")
                    continue
                
                comparison = backtest_result.get('comparison', {})
                service_levels = comparison.get('service_level', {})
                total_costs = comparison.get('total_cost', {})
                holding_costs = comparison.get('total_holding_cost', {})
                shortage_costs = comparison.get('total_shortage_cost', {})
                stockout_probs = comparison.get('stockout_probability', {})
                total_shortages = comparison.get('total_shortage', {})
                
                best_strategy = backtest_result.get('recommendation', {}).get('best_strategy', 'hybrid')
                
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
                
                service_level = service_levels.get(best_strategy, 0)
                total_cost = total_costs.get(best_strategy, 0)
                stockout_prob = stockout_probs.get(best_strategy, 0) if stockout_probs else 0
                total_shortage = total_shortages.get(best_strategy, 0) if total_shortages else 0
                
                tail_risk = min(1.0, stockout_prob * 2.5)
                if tail_risk > 0.6:
                    tail_risk_level = "🔴 Yüksek"
                elif tail_risk > 0.3:
                    tail_risk_level = "🟡 Orta"
                else:
                    tail_risk_level = "🟢 Düşük"
                
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
                    'recommended_rop': recommended_rop,
                    'pattern': 'DEGISKEN',
                    'cv': round(np.std(demand) / np.mean(demand) if np.mean(demand) > 0 else 0, 4)
                })
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                print(f"❌ Async backtest hatası ({material.get('code', '')}): {e}")
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
            'test_window': test_window,
            'strategies_tested': strategies_to_test,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Backtest tamamlandı!',
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
        
        db.commit()
        
        # Bildirim oluştur
        try:
            notification = Notification(
                user_id=user_id,
                title=f"✅ Backtest Analizi Tamamlandı!",
                message=f"Backtest raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
                type="success",
                link="/tasks"
            )
            db.add(notification)
            db.commit()
        except Exception as e:
            print(f"⚠️ Bildirim hatası: {e}")
        
        print(f"✅ Async backtest tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async backtest hatası: {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()
