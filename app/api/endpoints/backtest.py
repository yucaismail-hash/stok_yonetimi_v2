# app/api/endpoints/backtest.py - TAM VE GÜNCEL (ACTIVE DATASET BAZLI)

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.analysis.backtest import BacktestEngine
from app.auth import get_current_user
from app.models import User, AnalysisResult, Notification
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import numpy as np
import uuid
from app.analysis.trend_summary_engine import TrendSummaryEngine
from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country
import logging
from app.services.active_dataset import get_active_dataset_service
from app.services.pricing_engine import PricingEngine
from app.schemas.credit import PricingRequest
from app.services.dashboard_summary_builder import (
    build_forecast_dashboard_summary,
    build_safety_stock_dashboard_summary,
    build_simulation_dashboard_summary,
    build_backtest_dashboard_summary,
    build_supplier_dashboard_summary
)

logger = logging.getLogger(__name__)

router = APIRouter()
backtest_engine = BacktestEngine()
ai_engine = AISummaryEngine()


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


def validate_backtest_data(materials: list, test_window: int) -> tuple:
    """
    Backtest için verileri validate eder.
    Literatür: En az 8 hafta veri gereklidir.
    test_window + 4 hafta buffer (en az 8 hafta)
    """
    if not materials:
        return False, "Hiç malzeme verisi bulunamadı!", 0, 0
    
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
    
    min_required = max(8, test_window + 4)
    
    if max_weeks < min_required:
        return False, f"Yetersiz veri! Yüklenen en uzun veri {max_weeks} hafta, backtest için en az {min_required} hafta gerekiyor.", min_required, max_weeks
    
    return True, f"Veri yeterli ({max_weeks} hafta)", min_required, max_weeks


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
            
            recent_analyses = trend_engine.get_recent_analyses(db, user_id)
            if not recent_analyses:
                logger.info(f"ℹ️ Trend için yeterli analiz yok: {user_id}")
                return
            
            trend_summary = trend_engine.build_trend_summary(recent_analyses)
            
            executive_summary = exec_engine.build_executive_summary(
                trend_summary=trend_summary,
                previous_executive=user.executive_summary
            )
            
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


# ============================================================
# 📌 SENKRON BACKTEST - ACTIVE DATASET BAZLI
# ============================================================

@router.post("/backtest/batch")
def run_backtest_batch(
    request: BacktestBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Backtest analizi - ACTIVE DATASET BAZLI!
    """
    try:
        # ✅ ACTIVE DATASET'ten verileri al
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(current_user.id)
        
        if not stats['has_data']:
            raise HTTPException(
                status_code=404, 
                detail="Aktif dataset bulunamadı! Lütfen önce Excel yükleyip dataset oluşturun."
            )
        
        upload_id = stats['upload_id']
        dataset_id = stats['dataset_id']
        
        # ✅ Active dataset'ten materials'i al
        materials = active_service.get_active_materials(current_user.id)
        if not materials:
            raise HTTPException(status_code=404, detail="Dataset'te malzeme bulunamadı!")
        
        # ✅ Active dataset'i al (pricing için)
        dataset = active_service.get_active_dataset(current_user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Aktif dataset bulunamadı!")
        
        # ✅ Pricing Engine ile ücretlendirme
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/backtest/batch",
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
        
        # ✅ Analizi çalıştır
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
        
        # ✅ 1. result_data
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'test_window': test_window,
            'strategies_tested': strategies_to_test
        }
        
        # ✅ 2. AnalysisResult oluştur
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='backtest_batch',
            data=result_data,
            params={
                'test_window': test_window,
                'strategies_tested': len(strategies_to_test),
                'total_materials': len(results),
                'processing_score': pricing_response.processing_score,
                'credit_cost': pricing_response.credit_cost
            },
            total_materials=len(results),
            task_id=None,
            status=None,
            progress=100,
            expires_at=datetime.utcnow() + timedelta(days=15)
        )
        
        # ✅ 3. Kaydet ve ID al
        db.add(analysis_result)
        db.commit()
        db.refresh(analysis_result)
        
        # ✅ 4. dashboard_summary oluştur
        dashboard_summary = build_backtest_dashboard_summary(
            results=results,
            analysis_id=analysis_result.id,
            dataset_id=dataset.id,
            test_window=test_window
        )
        
        # ✅ 5. Güncelle
        result_data['dashboard_summary'] = dashboard_summary
        analysis_result.data = result_data
        db.commit()
        
        # AI Özetini arka planda oluştur
        background_tasks.add_task(
            generate_ai_summary_background,
            analysis_result.id,
            'backtest_batch',
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
            'ai_status': 'pending'
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
# 📌 ASYNC BACKTEST - ACTIVE DATASET BAZLI
# ============================================================

@router.post("/backtest/batch/async")
def start_async_backtest(
    request: BacktestBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Async backtest başlatır. Hemen task_id döner.
    ACTIVE DATASET BAZLI!
    """
    try:
        # ✅ ACTIVE DATASET'ten verileri al
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(current_user.id)
        
        if not stats['has_data']:
            raise HTTPException(
                status_code=404, 
                detail="Aktif dataset bulunamadı! Lütfen önce Excel yükleyip dataset oluşturun."
            )
        
        upload_id = stats['upload_id']
        dataset_id = stats['dataset_id']
        
        # ✅ Active dataset'ten materials'i al
        materials = active_service.get_active_materials(current_user.id)
        if not materials:
            raise HTTPException(status_code=404, detail="Dataset'te malzeme bulunamadı!")
        
        # ✅ Active dataset'i al (pricing için)
        dataset = active_service.get_active_dataset(current_user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Aktif dataset bulunamadı!")
        
        print(f"✅ Async backtest başlatılıyor: {len(materials)} malzeme")
        
        # ✅ Pricing Engine ile ücretlendirme (Async'de hemen düş)
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/backtest/batch/async",
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
        
        # Task ID oluştur
        task_id = str(uuid.uuid4())
        
        test_window = request.test_window or 8
        strategies = request.strategies
        
        all_strategies = ['ai', 'classic', 'croston', 'syntetos_boylan', 'ml', 'hybrid', 'simple_moving_avg', 'last_value']
        strategies_to_test = strategies if strategies else all_strategies
        
        # Initial record'u kaydet
        initial_data = {
            'status': 'processing',
            'message': 'Backtest başlatıldı, işleniyor...',
            'total': len(materials),
            'results': [],
            'test_window': test_window,
            'strategies': strategies,
            'task_id': task_id,
            'started_at': datetime.utcnow().isoformat(),
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score
        }
        
        initial_record = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='backtest_batch_async',
            data=initial_data,
            params={
                'test_window': test_window,
                'strategies_tested': len(strategies_to_test),
                'total_materials': len(materials),
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
        
        # Async job'u arka planda başlat
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
            "credit_cost": pricing_response.credit_cost,
            "balance_after": pricing_response.balance_after,
            "processing_score": pricing_response.processing_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Async Backtest başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC BACKTEST JOB - ACTIVE DATASET BAZLI
# ============================================================

def run_async_backtest_job(task_id: str, user_id: int, upload_id: str, request: BacktestBatchRequest, db: Session):
    """Async backtest işini gerçekleştirir - ACTIVE DATASET BAZLI!"""
    try:
        print(f"🔄 Async backtest başladı: Task ID {task_id}")
        
        # ✅ ACTIVE DATASET'ten verileri al
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(user_id)
        
        if not stats['has_data']:
            update_async_task_status(db, task_id, 'failed', 'Aktif dataset bulunamadı')
            return
        
        materials = active_service.get_active_materials(user_id)
        if not materials:
            update_async_task_status(db, task_id, 'failed', 'Dataset\'te malzeme bulunamadı')
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
        
        # ✅ 1. result_data hazırla
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
        
        # ✅ 2. Mevcut kaydı al
        existing = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if existing:
            # ✅ 3. dashboard_summary oluştur
            dashboard_summary = build_backtest_dashboard_summary(
                results=results,
                analysis_id=existing.id,
                dataset_id=0,
                test_window=test_window
            )
            
            # ✅ 4. dashboard_summary'yi ekle
            result_data['dashboard_summary'] = dashboard_summary
            
            # ✅ 5. Güncelle
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
        
        # ✅ AI SUMMARY + TREND + EXECUTIVE
        try:
            user = db.query(User).filter(User.id == user_id).first()
            country = user.billing_country if user else 'TR'
            language = get_language_from_country(country)
            
            result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
            
            if result:
                result_type = result.result_type
                
                engine = AISummaryEngine(language=language)
                summary = engine.build_summary(result_type, result.data)
                
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
                result.data = result_data
                
                db.commit()
                logger.info(f"✅ Async AI özeti tamamlandı: {task_id}")
                
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
        
        print(f"✅ Async backtest tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async backtest hatası: {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()