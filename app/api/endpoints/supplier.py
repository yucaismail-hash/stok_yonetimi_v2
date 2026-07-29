# app/api/endpoints/supplier.py - TAM VE GÜNCEL (DÜZELTİLMİŞ)

import numpy as np
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
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
from app.models import User, AnalysisResult, Notification
from app.database import get_db
from sqlalchemy.orm import Session
from app.services.active_dataset import get_active_dataset_service
from app.services.pricing_engine import PricingEngine
from app.schemas.credit import PricingRequest

from app.analysis.trend_summary_engine import TrendSummaryEngine
from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
from app.analysis.ai_summary_engine import AISummaryEngine, get_language_from_country
import uuid
import logging
from app.services.learning_engine import LearningEngine
from app.services.ai.ai_decision_engine import AIDecisionEngine
from app.services.dashboard_builder import get_dashboard_builder

logger = logging.getLogger(__name__)

router = APIRouter()

supplier_analyzer = SupplierPerformanceAnalyzer()
share_optimizer = SupplierShareOptimizer(supplier_analyzer)
ai_engine = AISummaryEngine()


# ============================================================
# 📌 YARDIMCI FONKSİYONLAR
# ============================================================

def update_async_task_status(db: Session, task_id: str, status: str, message: str):
    """Async task status'ünü günceller - task_id ile arar"""
    try:
        result = db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id
        ).first()
        
        if result:
            # ✅ Mevcut kaydı güncelle
            result.status = status
            result.message = message
            result.updated_at = datetime.utcnow()
            db.commit()
            print(f"✅ Task {task_id} durumu güncellendi: {status}")
        else:
            # ❌ Kayıt bulunamadı - yeni kayıt oluştur
            print(f"⚠️ Task {task_id} için kayıt bulunamadı, yeni oluşturuluyor...")
            # Bu durumda yeni kayıt oluşturulabilir veya loglanabilir
            # Şimdilik sadece loglayalım
    except Exception as e:
        print(f"❌ update_async_task_status hatası: {e}")
        db.rollback()


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
        from app.analysis.trend_summary_engine import TrendSummaryEngine
        from app.analysis.executive_summary_engine import ExecutiveSummaryEngine
        from app.analysis.ai_summary_engine import get_language_from_country
        
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"❌ Kullanıcı bulunamadı: {user_id}")
                return
            
            language = get_language_from_country(country or user.billing_country or "TR")
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
            
            # AI Decision alanlarını güncelle
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
# 📌 SENKRON TEDARİKÇİ ANALİZİ - ACTIVE DATASET BAZLI
# ============================================================

# app/api/endpoints/supplier.py - analyze_suppliers_batch (TAM DÜZELTİLMİŞ)

@router.post("/supplier/batch")
def analyze_suppliers_batch(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toplu Tedarikçi Analizi - ACTIVE DATASET BAZLI!
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
        
        # ✅ Active dataset'ten verileri al
        suppliers = active_service.get_active_suppliers(current_user.id)
        supplier_mapping = active_service.get_active_supplier_mapping(current_user.id)
        materials = active_service.get_active_materials(current_user.id)
        
        # ✅ Active dataset'i al (pricing için)
        dataset = active_service.get_active_dataset(current_user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Aktif dataset bulunamadı!")
        
        # ✅ Verileri kontrol et
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
        
        # ✅ Pricing Engine ile ücretlendirme
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/supplier/batch",
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
        supplier_results = []
        recommendations = []
        
        for supplier_id, supplier_data in suppliers.items():
            name = supplier_data.get('name', supplier_id)
            factor = supplier_data.get('factor', 1.0)
            ontime_rate = supplier_data.get('ontime_rate', 0.8)
            
            # ✅ lt_mean ve lt_std None kontrolü
            lt_mean = supplier_data.get('lt_mean')
            if lt_mean is None:
                lt_mean = 14
            
            lt_std = supplier_data.get('lt_std')
            if lt_std is None:
                lt_std = 3
            
            risk_score = 1.0 - ontime_rate
            perf_score = ontime_rate * (1.0 / factor) if factor > 0 else ontime_rate
            
            material_count = 0
            total_share = 0
            for mat_code, mappings in supplier_mapping.items():
                for m in mappings:
                    if m.get('supplier_id') == supplier_id:
                        material_count += 1
                        total_share += m.get('share', 0)
            
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
            
            # ✅ lt_mean ve lt_std formatlanırken None kontrolü
            recommendation_parts.append(f"⏱️ Ortalama LT: {float(lt_mean):.0f} gün (Std: {float(lt_std):.0f})")
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
            
            if risk_score < 0.15 and perf_score > 0.85:
                recommendations.append(f"✅ {name}: Tercih edilen tedarikçi")
            elif risk_score > 0.4:
                recommendations.append(f"⚠️ {name}: Yüksek risk, alternatif değerlendir")
        
        if len(supplier_results) > 1:
            best_supplier = min(supplier_results, key=lambda x: x['risk_score'] * x['factor'])
            share_advice = []
            for s in supplier_results:
                if s['supplier_id'] == best_supplier['supplier_id']:
                    share_advice.append(f"{s['name']}: %70-%80")
                elif s['risk_score'] < 0.3:
                    share_advice.append(f"{s['name']}: %15-%25")
                else:
                    share_advice.append(f"{s['name']}: %5-%10 (alternatif)")
            recommendations.append("📊 Pay Dağılım Önerisi: " + " | ".join(share_advice))
        
        if not supplier_results:
            raise HTTPException(status_code=400, detail="Hiçbir sonuç üretilemedi!")
        
        # ✅ 1. result_data
        result_data = {
            'suppliers': supplier_results,
            'recommendations': recommendations,
            'total_suppliers': len(supplier_results),
            'has_suppliers': True
        }
        
        # ✅ 2. AnalysisResult oluştur
        analysis_result = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='supplier_batch',
            data=result_data,
            params={
                'total_suppliers': len(supplier_results),
                'processing_score': pricing_response.processing_score,
                'credit_cost': pricing_response.credit_cost
            },
            total_materials=len(supplier_results),
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
            result_type='supplier_batch',
            analysis_id=analysis_result.id,
            ai_decision=result_data.get('ai_decision', {}),
            data=result_data
        )
        
        # ✅ 5. dashboard_summary'yi ekle ve güncelle
        result_data['dashboard_summary'] = dashboard_summary
        analysis_result.data = result_data
        db.commit()
        
        # ✅ AI Decision'ı arka planda oluştur (AI Summary'dan sonra)
        background_tasks.add_task(
            generate_ai_decision_background,
            analysis_result.id,
            'supplier_batch',
            current_user.id,
            current_user.billing_country or 'TR'
        )
        
        # ✅ Learning Engine'i arka planda tetikle (mevcut kodun sonuna ekleyin)
        background_tasks.add_task(
            trigger_learning_engine_background,
            current_user.id,
            analysis_result.id,
            'supplier_batch'
        )
        
        return {
            'success': True,
            'total_suppliers': len(supplier_results),
            'suppliers': supplier_results,
            'recommendations': recommendations,
            'has_suppliers': True,
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
        logger.error(f"❌ Tedarikçi analiz hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# 📌 SENKRON TEDARİKÇİ KONTROL - ACTIVE DATASET BAZLI
# ============================================================

@router.get("/supplier/check")
def check_supplier_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tedarikçi verisi kontrolü - ACTIVE DATASET BAZLI!"""
    try:
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(current_user.id)
        
        if not stats['has_data']:
            return {
                'has_suppliers': False,
                'message': 'Aktif dataset bulunamadı! Lütfen önce Excel yükleyip dataset oluşturun.'
            }
        
        suppliers = active_service.get_active_suppliers(current_user.id)
        supplier_mapping = active_service.get_active_supplier_mapping(current_user.id)
        
        has_suppliers = bool(suppliers) and bool(supplier_mapping)
        
        return {
            'has_suppliers': has_suppliers,
            'supplier_count': len(suppliers),
            'mapping_count': len(supplier_mapping),
            'message': 'Tedarikçi verileri mevcut' if has_suppliers else 'Tedarikçi verisi bulunamadı.'
        }
        
    except Exception as e:
        logger.error(f"❌ Tedarikçi kontrol hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 SENKRON TEDARİKÇİ RİSK
# ============================================================

@router.get("/supplier/{supplier_id}/risk")
def get_supplier_risk(
    supplier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Tedarikçi risk skorunu getirir - ACTIVE DATASET BAZLI!"""
    try:
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(current_user.id)
        
        if not stats['has_data']:
            raise HTTPException(status_code=404, detail="Aktif dataset bulunamadı!")
        
        suppliers = active_service.get_active_suppliers(current_user.id)
        
        if supplier_id not in suppliers:
            raise HTTPException(status_code=404, detail=f"Tedarikçi '{supplier_id}' bulunamadı!")
        
        supplier_data = suppliers[supplier_id]
        ontime_rate = supplier_data.get('ontime_rate', 0.8)
        factor = supplier_data.get('factor', 1.0)
        
        risk_score = 1.0 - ontime_rate
        perf_score = ontime_rate * (1.0 / factor) if factor > 0 else ontime_rate
        
        return {
            "supplier_id": supplier_id,
            "risk_score": risk_score,
            "performance_score": perf_score,
            "risk_level": "YÜKSEK" if risk_score > 0.4 else ("ORTA" if risk_score > 0.2 else "DÜŞÜK"),
            "performance_level": "İYİ" if perf_score > 0.7 else ("ORTA" if perf_score > 0.4 else "KÖTÜ")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Tedarikçi risk hatası: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC TEDARİKÇİ ANALİZİ - ACTIVE DATASET BAZLI
# ============================================================

@router.post("/supplier/batch/async")
def start_async_supplier_analysis(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Async tedarikçi analizi başlatır. Hemen task_id döner.
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
        
        # ✅ Active dataset'ten verileri al
        suppliers = active_service.get_active_suppliers(current_user.id)
        supplier_mapping = active_service.get_active_supplier_mapping(current_user.id)
        
        if not suppliers or not supplier_mapping:
            raise HTTPException(
                status_code=400, 
                detail="Tedarikçi verisi bulunamadı. Lütfen Excel'de 'Tedarikciler' ve 'Malzeme_Tedarikciler' sheet'lerini ekleyin."
            )
        
        # ✅ Active dataset'i al (pricing için)
        dataset = active_service.get_active_dataset(current_user.id)
        if not dataset:
            raise HTTPException(status_code=404, detail="Aktif dataset bulunamadı!")
        
        # ✅ Pricing Engine ile ücretlendirme (Async'de hemen düş)
        pricing_engine = PricingEngine(db)
        pricing_request = PricingRequest(
            endpoint="/api/supplier/batch/async",
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
            'message': 'Tedarikçi analizi başlatıldı, işleniyor...',
            'total': len(suppliers),
            'total_suppliers': len(suppliers),
            'results': [],
            'task_id': task_id,
            'started_at': datetime.utcnow().isoformat(),
            'credit_cost': pricing_response.credit_cost,
            'balance_after': pricing_response.balance_after,
            'processing_score': pricing_response.processing_score
        }
        
        initial_record = AnalysisResult(
            user_id=current_user.id,
            upload_id=upload_id,
            result_type='supplier_batch_async',
            data=initial_data,
            params={
                'total_suppliers': len(suppliers),
                'credit_cost': pricing_response.credit_cost,
                'processing_score': pricing_response.processing_score
            },
            total_materials=len(suppliers),
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
            run_async_supplier_job,
            task_id=task_id,
            user_id=current_user.id,
            upload_id=upload_id,
            db=db
        )
        
        return {
            "task_id": task_id,
            "status": "started",
            "message": "Tedarikçi analizi arka planda başlatıldı.",
            "credit_cost": pricing_response.credit_cost,
            "balance_after": pricing_response.balance_after,
            "processing_score": pricing_response.processing_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Async Tedarikçi analizi başlatma hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================
# 📌 ASYNC TEDARİKÇİ ANALİZİ JOB - ACTIVE DATASET BAZLI
# ============================================================

# app/api/endpoints/supplier.py - run_async_supplier_job (DÜZELTİLDİ)

def run_async_supplier_job(task_id: str, user_id: int, upload_id: str, db: Session):
    """Async tedarikçi analizi işini gerçekleştirir - ACTIVE DATASET BAZLI!"""
    try:
        print(f"🔄 Async tedarikçi analizi başladı: Task ID {task_id}")
        
        # ✅ ACTIVE DATASET'ten verileri al (cached_data KULLANMA!)
        active_service = get_active_dataset_service(db)
        stats = active_service.get_dataset_stats(user_id)
        
        if not stats['has_data']:
            update_async_task_status(db, task_id, 'failed', 'Aktif dataset bulunamadı')
            return
        
        suppliers = active_service.get_active_suppliers(user_id)
        supplier_mapping = active_service.get_active_supplier_mapping(user_id)
        
        if not suppliers or not supplier_mapping:
            update_async_task_status(db, task_id, 'failed', 'Tedarikçi verisi bulunamadı')
            return
        
        supplier_results = []
        recommendations = []
        
        for supplier_id, supplier_data in suppliers.items():
            name = supplier_data.get('name', supplier_id)
            factor = supplier_data.get('factor', 1.0)
            ontime_rate = supplier_data.get('ontime_rate', 0.8)
            
            # ✅ lt_mean ve lt_std None kontrolü
            lt_mean = supplier_data.get('lt_mean')
            if lt_mean is None:
                lt_mean = 14
            
            lt_std = supplier_data.get('lt_std')
            if lt_std is None:
                lt_std = 3
            
            risk_score = 1.0 - ontime_rate
            perf_score = ontime_rate * (1.0 / factor) if factor > 0 else ontime_rate
            
            material_count = 0
            total_share = 0
            for mat_code, mappings in supplier_mapping.items():
                for m in mappings:
                    if m.get('supplier_id') == supplier_id:
                        material_count += 1
                        total_share += m.get('share', 0)
            
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
            
            recommendation_parts.append(f"⏱️ Ortalama LT: {float(lt_mean):.0f} gün (Std: {float(lt_std):.0f})")
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
            
            if risk_score < 0.15 and perf_score > 0.85:
                recommendations.append(f"✅ {name}: Tercih edilen tedarikçi")
            elif risk_score > 0.4:
                recommendations.append(f"⚠️ {name}: Yüksek risk, alternatif değerlendir")
        
        if len(supplier_results) > 1:
            best_supplier = min(supplier_results, key=lambda x: x['risk_score'] * x['factor'])
            share_advice = []
            for s in supplier_results:
                if s['supplier_id'] == best_supplier['supplier_id']:
                    share_advice.append(f"{s['name']}: %70-%80")
                elif s['risk_score'] < 0.3:
                    share_advice.append(f"{s['name']}: %15-%25")
                else:
                    share_advice.append(f"{s['name']}: %5-%10 (alternatif)")
            recommendations.append("📊 Pay Dağılım Önerisi: " + " | ".join(share_advice))
        
        if not supplier_results:
            update_async_task_status(db, task_id, 'failed', 'Hiçbir sonuç üretilemedi')
            return
        
                # ✅ 1. result_data hazırla
        result_data = {
            'success': True,
            'total': len(supplier_results),
            'suppliers': supplier_results,
            'recommendations': recommendations,
            'total_suppliers': len(supplier_results),
            'has_suppliers': True,
            'task_id': task_id,
            'status': 'completed',
            'message': 'Tedarikçi analizi tamamlandı!',
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
                result_type='supplier_batch_async',
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
                'total_materials': len(supplier_results),
                'updated_at': datetime.utcnow()
            })
            db.commit()
        
        # ✅ 6. Trend Summary yenile
        try:
            refresh_trend_summary(user_id, country)
            logger.info(f"✅ Async Trend Summary yenilendi: {task_id}")
        except Exception as e:
            logger.error(f"❌ Async Trend Summary hatası: {e}")
        
        # ✅ 7. AI DECISION + LEARNING ENGINE (YENİ)
        try:
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
        
        print(f"✅ Async tedarikçi analizi tamamlandı: Task ID {task_id}, {len(supplier_results)} tedarikçi")
        
    except Exception as e:
        print(f"❌ Async tedarikçi analizi hatası: {e}")
        import traceback
        traceback.print_exc()
        update_async_task_status(db, task_id, 'failed', str(e))
        db.rollback()
