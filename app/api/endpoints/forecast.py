# app/api/endpoints/forecast.py - TAM VE GÜNCEL (ACTIVE DATASET BAZLI)

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
import os
import requests
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult, Notification
from app.services.active_dataset import get_active_dataset_service
from app.services.pricing_engine import PricingEngine
from app.schemas.credit import PricingRequest
from app.analysis.trend_summary_engine import TrendSummaryEngine
from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
from app.analysis.forecast import DemandForecaster
from app.analysis.pattern import AdvancedDemandAnalyzer
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country
from app.services.llm_service import get_llm_service
from app.auth import get_current_user
from datetime import datetime, timedelta
import numpy as np
import logging

from app.api.dependencies import (
    get_or_create_dataset_from_upload,
    process_pricing_with_dataset,
    get_active_dataset
)
from app.services.learning_engine import LearningEngine
from app.services.ai.ai_decision_engine import AIDecisionEngine
from app.services.dashboard_builder import get_dashboard_builder

logger = logging.getLogger(__name__)

router = APIRouter()

# Pattern analizci ile forecast'u zenginleştir
pattern_analyzer = AdvancedDemandAnalyzer()
forecaster = DemandForecaster(seasonal_periods=52)
forecaster.set_pattern_analyzer(pattern_analyzer)

# AI Engine instance
ai_engine = AISummaryEngine()


class ForecastRequest(BaseModel):
    horizon: int = 13
    model_type: str = "auto"


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
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


def generate_ai_summary_background(
    result_id: int,
    result_type: str,
    user_id: int,
    country: str = "TR"
):
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
                
                if summary.get("_error"):
                    logger.warning(f"⚠️ AI özeti hata ile tamamlandı: {summary.get('_error')}")
                
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

def generate_ai_decision_background(result_id: int, result_type: str, user_id: int, country: str = "TR"):
    """
    Arka planda AI Decision Engine ile karar oluşturur.
    """
    try:
        from app.database import SessionLocal
        from app.models import User, AnalysisResult
        from app.services.ai.ai_decision_engine import AIDecisionEngine
        from app.analysis.ai_summary_engine import get_language_from_country
        
        db2 = SessionLocal()
        try:
            user = db2.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"❌ Kullanıcı bulunamadı: {user_id}")
                return
            
            result = db2.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            if not result:
                logger.error(f"❌ Analiz sonucu bulunamadı: {result_id}")
                return
            
            language = get_language_from_country(country or user.billing_country or "TR")
            
            # AI Decision Engine ile karar oluştur
            decision_engine = AIDecisionEngine(language=language)
            decision = decision_engine.generate_decision(
                analysis_type=result_type,
                analysis_data=result.data
            )
            
            # Kararı veriye ekle
            data = result.data or {}
            data['ai_decision'] = decision
            result.data = data
            
            result.ai_status = "decision_completed"
            result.ai_created_at = datetime.utcnow()
            db2.commit()
            
            logger.info(f"✅ AI Decision oluşturuldu: {result_type} (ID: {result_id})")
            
            # ✅ Learning Engine'i tetikle
            try:
                learning_engine = LearningEngine(db2, user_id)
                learning_engine.analyze_and_learn({
                    'result_type': result_type,
                    'data': result.data
                })
                logger.info(f"✅ Learning Engine tamamlandı: {result_id}")
            except Exception as e:
                logger.error(f"❌ Learning Engine hatası: {e}")
            
        finally:
            db2.close()
    except Exception as e:
        logger.error(f"❌ AI Decision oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()

def trigger_learning_engine_background(user_id: int, result_id: int, result_type: str):
    """
    Arka planda Learning Engine'i tetikler.
    """
    try:
        from app.database import SessionLocal
        from app.models import AnalysisResult
        from app.services.learning_engine import LearningEngine
        
        db = SessionLocal()
        try:
            result = db.query(AnalysisResult).filter(AnalysisResult.id == result_id).first()
            if result:
                engine = LearningEngine(db, user_id)
                engine.analyze_and_learn({
                    'result_type': result_type,
                    'data': result.data
                })
                logger.info(f"✅ Learning Engine tetiklendi: {result_id}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"❌ Learning Engine background hatası: {e}")

# ============================================================
# 📌 SENKRON FORECAST - ACTIVE DATASET BAZLI
# ============================================================

@router.post("/forecast/batch")
def batch_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu forecast analizi - ACTIVE DATASET BAZLI!
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
            endpoint="/api/forecast/batch",
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
        results = []
        for material in materials:
            try:
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(historical)
                
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                model_comparison = {}
                for model_name in ['holt_winters', 'arima', 'simple']:
                    try:
                        if model_name == 'holt_winters' and len(historical) >= 12:
                            model_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        elif model_name == 'arima' and len(historical) >= 8:
                            model_result = forecaster.arima_forecast(historical, request.horizon)
                        else:
                            model_result = forecaster.simple_forecast(historical, request.horizon)
                        
                        rmse = forecaster.calculate_model_rmse(historical, model_result.get('mean', []))
                        model_comparison[model_name] = {
                            'rmse': rmse,
                            'forecast': model_result.get('mean', [])
                        }
                    except:
                        pass
                
                outlier_info = forecaster.detect_outliers(historical)
                
                trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                
                model_params = {}
                if forecast_result.get('model_used') == 'holt_winters':
                    model_params = {
                        'seasonal_periods': 52,
                        'trend': 'add',
                        'seasonal': 'add'
                    }
                elif forecast_result.get('model_used') == 'arima':
                    model_params = {
                        'order': '(1,1,1)',
                        'seasonal_order': None
                    }
                elif forecast_result.get('model_used') == 'simple':
                    model_params = {
                        'window': 4,
                        'weighted': True
                    }
                
                if 'selection_info' in forecast_result:
                    model_params.update(forecast_result['selection_info'])
                
                model_params['pattern'] = pattern
                model_params['pattern_label'] = get_pattern_label(pattern)
                model_params['pattern_color'] = get_pattern_color(pattern)
                model_params['cv'] = round(pattern_stats.get('cv', 0), 4)
                model_params['zero_ratio'] = round(pattern_stats.get('zero_ratio', 0), 4)
                
                selection_reason = forecast_result.get('selection_info', {}).get('selection_reason', 'Otomatik seçim')
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': request.horizon,
                    'selected_model': forecast_result.get('model_used', 'simple'),
                    'best_model_label': forecast_result.get('model_used', 'simple').replace('_', ' ').title(),
                    'model_description': f"{forecast_result.get('model_used', 'simple')} modeli kullanıldı",
                    'selection_reason': selection_reason,
                    'forecast': forecast_result.get('mean', []),
                    'lower_80': forecast_result.get('lower_80', []),
                    'upper_80': forecast_result.get('upper_80', []),
                    'lower_95': forecast_result.get('lower_95', []),
                    'upper_95': forecast_result.get('upper_95', []),
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': forecaster.calculate_model_rmse(historical, forecast_result.get('mean', [])),
                    'model_comparison': model_comparison,
                    'model_params': model_params,
                    'outlier_info': outlier_info,
                    'historical_data': historical,
                    'pattern': pattern,
                    'pattern_label': get_pattern_label(pattern),
                    'pattern_color': get_pattern_color(pattern),
                    'cv': round(pattern_stats.get('cv', 0), 4),
                    'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4)
                })
                
            except Exception as e:
                logger.error(f"❌ Malzeme {material.get('code', '')} tahmin hatası: {e}")
                continue
        
        if not results:
            raise HTTPException(status_code=400, detail="Hiçbir malzeme için tahmin yapılamadı!")
        
                # ✅ 1. result_data hazırla (dashboard_summary OLMADAN)
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'horizon': request.horizon,
            'model_type': request.model_type,
            'pattern_analysis': True
        }
        
        # ✅ 2. AnalysisResult oluştur
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='forecast_batch',
            data=result_data,
            params={
                'horizon': request.horizon,
                'model_type': request.model_type,
                'total_materials': len(results),
                'pattern_analysis': True,
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
        
        # ✅ 4. YENİ: Dashboard Builder ile summary oluştur
        builder = get_dashboard_builder(db, current_user.id)
        dashboard_summary = builder._build_summary_from_decision(
            result_type='forecast_batch',
            analysis_id=analysis_result.id,
            ai_decision=result_data.get('ai_decision', {}),
            data=result_data
        )
        
        # ✅ 5. dashboard_summary'yi ekle ve güncelle
        result_data['dashboard_summary'] = dashboard_summary
        analysis_result.data = result_data
        db.commit()
        
        # Öğrenme verilerini güncelle
        if results:
            from app.api.endpoints.learning import update_learning_from_pattern
            pattern_results = [
                {
                    'material_code': r.get('material_code'),
                    'group': r.get('group'),
                    'pattern': r.get('pattern'),
                    'cv': r.get('cv'),
                    'zero_ratio': r.get('zero_ratio'),
                    'trend': r.get('trend_direction'),
                }
                for r in results
            ]
            update_learning_from_pattern(current_user.id, pattern_results, db)
        
        db.commit()
        db.refresh(analysis_result)
        
        # ✅ AI Decision'ı arka planda oluştur (AI Summary'dan sonra)
        background_tasks.add_task(
            generate_ai_decision_background,
            analysis_result.id,
            'forecast_batch',
            current_user.id,
            current_user.billing_country or 'TR'
        )
        
        # ✅ Learning Engine'i arka planda tetikle
        background_tasks.add_task(
            trigger_learning_engine_background,
            current_user.id,
            analysis_result.id,
            'forecast_batch'
        )
        
        return {
            'success': True,
            'total': len(results),
            'results': results,
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score,
            'result_id': analysis_result.id,
            'pattern_analysis': True,
            'ai_status': 'pending'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Forecast hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC FORECAST - ACTIVE DATASET BAZLI
# ============================================================

@router.post("/forecast/batch/async")
def start_async_forecast(
    request: ForecastRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Async forecast - ACTIVE DATASET BAZLI!
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
        
        # ✅ Pricing Engine ile ücretlendirme (Async'de hemen düş)
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/forecast/batch/async",
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
        
        # Initial record'u kaydet
        initial_data = {
            'status': 'processing',
            'message': 'Forecast analizi başlatıldı...',
            'total': len(materials),
            'results': [],
            'horizon': request.horizon,
            'model_type': request.model_type,
            'task_id': task_id,
            'pattern_analysis': True,
            'started_at': datetime.utcnow().isoformat(),
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score
        }
        
        initial_record = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='forecast_batch_async',
            data=initial_data,
            params={
                'horizon': request.horizon,
                'model_type': request.model_type,
                'total_materials': len(materials),
                'pattern_analysis': True,
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
            run_async_forecast_job,
            task_id=task_id,
            user_id=current_user.id,
            upload_id=upload_id,
            request=request,
            db=db
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Forecast analizi arka planda başlatıldı.",
            "credit_cost": pricing_response.credit_cost,
            "balance_after": pricing_response.balance_after,
            "processing_score": pricing_response.processing_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Async Forecast başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC FORECAST JOB - ACTIVE DATASET BAZLI
# ============================================================

# app/api/endpoints/forecast.py - ASYNC JOB TAM GÜNCELLEME
# run_async_forecast_job fonksiyonunun TAMAMI


def run_async_forecast_job(task_id: str, user_id: int, upload_id: str, request: ForecastRequest, db: Session):
    """Async forecast işini gerçekleştirir - ACTIVE DATASET BAZLI!"""
    try:
        print(f"🔄 Async forecast başladı: Task ID {task_id}")
        
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
        
        results = []
        total = len(materials)
        
        for idx, material in enumerate(materials):
            try:
                historical = material.get('historical_demand', [])
                if len(historical) < 4:
                    continue
                
                pattern, pattern_stats = pattern_analyzer.analyze_demand_pattern(historical)
                
                forecast_result = forecaster.forecast(
                    historical_data=historical,
                    horizon=request.horizon,
                    model_type=request.model_type
                )
                
                model_comparison = {}
                for model_name in ['holt_winters', 'arima', 'simple']:
                    try:
                        if model_name == 'holt_winters' and len(historical) >= 12:
                            model_result = forecaster.holt_winters_forecast(historical, request.horizon)
                        elif model_name == 'arima' and len(historical) >= 8:
                            model_result = forecaster.arima_forecast(historical, request.horizon)
                        else:
                            model_result = forecaster.simple_forecast(historical, request.horizon)
                        
                        rmse = forecaster.calculate_model_rmse(historical, model_result.get('mean', []))
                        model_comparison[model_name] = {
                            'rmse': rmse,
                            'forecast': model_result.get('mean', [])
                        }
                    except:
                        pass
                
                outlier_info = forecaster.detect_outliers(historical)
                
                trend_percent = ((historical[-1] - historical[0]) / historical[0] * 100) if historical[0] > 0 else 0
                trend_direction = 'Artış' if trend_percent > 0 else 'Azalış'
                
                model_params = {}
                if forecast_result.get('model_used') == 'holt_winters':
                    model_params = {
                        'seasonal_periods': 52,
                        'trend': 'add',
                        'seasonal': 'add'
                    }
                elif forecast_result.get('model_used') == 'arima':
                    model_params = {
                        'order': '(1,1,1)',
                        'seasonal_order': None
                    }
                elif forecast_result.get('model_used') == 'simple':
                    model_params = {
                        'window': 4,
                        'weighted': True
                    }
                
                if 'selection_info' in forecast_result:
                    model_params.update(forecast_result['selection_info'])
                
                model_params['pattern'] = pattern
                model_params['pattern_label'] = get_pattern_label(pattern)
                model_params['pattern_color'] = get_pattern_color(pattern)
                model_params['cv'] = round(pattern_stats.get('cv', 0), 4)
                model_params['zero_ratio'] = round(pattern_stats.get('zero_ratio', 0), 4)
                
                selection_reason = forecast_result.get('selection_info', {}).get('selection_reason', 'Otomatik seçim')
                
                results.append({
                    'material_code': material.get('code', ''),
                    'group': material.get('group', 'GENEL'),
                    'horizon': request.horizon,
                    'selected_model': forecast_result.get('model_used', 'simple'),
                    'best_model_label': forecast_result.get('model_used', 'simple').replace('_', ' ').title(),
                    'model_description': f"{forecast_result.get('model_used', 'simple')} modeli kullanıldı",
                    'selection_reason': selection_reason,
                    'forecast': forecast_result.get('mean', []),
                    'lower_80': forecast_result.get('lower_80', []),
                    'upper_80': forecast_result.get('upper_80', []),
                    'lower_95': forecast_result.get('lower_95', []),
                    'upper_95': forecast_result.get('upper_95', []),
                    'trend_direction': trend_direction,
                    'trend_percent': round(trend_percent, 1),
                    'model_rmse': forecaster.calculate_model_rmse(historical, forecast_result.get('mean', [])),
                    'model_comparison': model_comparison,
                    'model_params': model_params,
                    'outlier_info': outlier_info,
                    'historical_data': historical,
                    'pattern': pattern,
                    'pattern_label': get_pattern_label(pattern),
                    'pattern_color': get_pattern_color(pattern),
                    'cv': round(pattern_stats.get('cv', 0), 4),
                    'zero_ratio': round(pattern_stats.get('zero_ratio', 0), 4)
                })
                
                progress = int((idx + 1) / total * 100)
                update_async_progress(db, task_id, progress, f'{progress}% tamamlandı', len(results))
                
            except Exception as e:
                logger.error(f"❌ Malzeme {material.get('code', '')} tahmin hatası (Task {task_id}): {e}")
                continue
        
        if not results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
        # ✅ 1. result_data hazırla
        result_data = {
            'success': True,
            'total': len(results),
            'results': results,
            'horizon': request.horizon,
            'model_type': request.model_type,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Forecast analizi tamamlandı!',
            'pattern_analysis': True,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        # ✅ 2. Mevcut kaydı al
        existing = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if existing:
            # ✅ 3. YENİ: Dashboard Builder ile summary oluştur
            builder = get_dashboard_builder(db, user_id)
            dashboard_summary = builder._build_summary_from_decision(
                result_type='forecast_batch_async',
                analysis_id=existing.id,
                ai_decision=result_data.get('ai_decision', {}),
                data=result_data
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
        
        # Öğrenme verilerini güncelle
        if results:
            from app.api.endpoints.learning import update_learning_from_pattern
            pattern_results = [
                {
                    'material_code': r.get('material_code'),
                    'group': r.get('group'),
                    'pattern': r.get('pattern'),
                    'cv': r.get('cv'),
                    'zero_ratio': r.get('zero_ratio'),
                    'trend': r.get('trend_direction'),
                }
                for r in results
            ]
            update_learning_from_pattern(user_id, pattern_results, db)
        
        db.commit()
        
        # ✅ Sonucu tekrar al (ID için)
        result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
        
        # ✅ Bildirim oluştur
        try:
            notification = Notification(
                user_id=user_id,
                title=f"✅ Talep Tahmini Tamamlandı!",
                message=f"Forecast raporunuz başarıyla oluşturuldu. (#{task_id[:8]})",
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
        
        # ✅ AI DECISION + LEARNING ENGINE (YENİ)
        try:
            result = db.query(AnalysisResult).filter(AnalysisResult.task_id == task_id).first()
            if result:
                from app.services.ai.ai_decision_engine import AIDecisionEngine
                from app.services.learning_engine import LearningEngine
                from app.analysis.ai_summary_engine import get_language_from_country
                
                user = db.query(User).filter(User.id == user_id).first()
                language = get_language_from_country(user.billing_country or "TR")
                
                # AI Decision oluştur
                decision_engine = AIDecisionEngine(language=language)
                decision = decision_engine.generate_decision(
                    analysis_type=result.result_type,
                    analysis_data=result.data
                )
                
                # Kararı veriye ekle
                data = result.data or {}
                data['ai_decision'] = decision
                result.data = data
                db.commit()
                logger.info(f"✅ Async AI Decision oluşturuldu: {task_id}")
                
                # Learning Engine'i tetikle
                learning_engine = LearningEngine(db, user_id)
                learning_engine.analyze_and_learn({
                    'result_type': result.result_type,
                    'data': result.data
                })
                db.commit()
                logger.info(f"✅ Async Learning Engine tamamlandı: {task_id}")
                
        except Exception as e:
            logger.error(f"❌ Async AI Decision/Learning hatası: {e}")
            db.query(AnalysisResult).filter(
                AnalysisResult.task_id == task_id
            ).update({
                'ai_status': 'decision_failed',
                'ai_created_at': datetime.utcnow(),
            })
            db.commit()
        
        print(f"✅ Async forecast tamamlandı: Task ID {task_id}, {len(results)} malzeme")
        
    except Exception as e:
        print(f"❌ Async forecast hatası (Task {task_id}): {e}")
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()
