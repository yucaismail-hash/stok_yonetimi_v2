# app/services/learning_score_service.py - GÜNCELLENDİ

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models import *

logger = logging.getLogger(__name__)


class LearningScoreService:
    """
    Learning Score Servisi - Şirket için öğrenme seviyesini hesaplar.
    """
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    def calculate_learning_score(self) -> Dict[str, Any]:
        """
        Öğrenme skorunu hesaplar.
        """
        try:
            components = {
                'analysis_count': self._score_analysis_count(),
                'verified_rules': self._score_verified_rules(),
                'data_quality': self._score_data_quality(),
                'forecast_accuracy': self._score_forecast_accuracy(),
                'ai_confidence': self._score_ai_confidence()
            }
            
            total_score = sum([comp['score'] for comp in components.values()])
            
            # ✅ Eğer tüm bileşenler 0 ise skor 0 olsun
            if total_score == 0:
                level = "Öğreniyor"
            else:
                level = self._get_level(total_score)
            
            logger.info(f"📊 Learning Score hesaplandı: User={self.user_id}, Score={total_score}, Level={level}")
            
            return {
                'score': total_score,
                'components': components,
                'level': level,
                'percentage': total_score
            }
            
        except Exception as e:
            logger.error(f"❌ Learning Score hesaplama hatası: {e}")
            return {
                'score': 0,
                'components': {
                    'analysis_count': {'score': 0, 'max': 30, 'value': 0, 'label': '0 analiz'},
                    'verified_rules': {'score': 0, 'max': 25, 'value': 0, 'label': '0 doğrulanmış kural'},
                    'data_quality': {'score': 0, 'max': 20, 'value': 0, 'label': 'Veri yok'},
                    'forecast_accuracy': {'score': 0, 'max': 15, 'value': 0, 'label': 'Forecast yok'},
                    'ai_confidence': {'score': 0, 'max': 10, 'value': 0, 'label': 'AI analizi yok'}
                },
                'level': 'Öğreniyor',
                'percentage': 0,
                'error': str(e)
            }
    
    def _score_analysis_count(self) -> Dict[str, Any]:
        """Analiz sayısı bileşeni (max 30)"""
        try:
            # ✅ status = 'completed' VEYA status IS NULL (senkron analizler için)
            from sqlalchemy import or_
            
            count = self.db.query(AnalysisResult).filter(
                AnalysisResult.user_id == self.user_id,
                or_(
                    AnalysisResult.status == 'completed',
                    AnalysisResult.status.is_(None)  # ✅ Senkron analizler için
                )
            ).count()
            
            logger.info(f"📊 Analiz sayısı: {count}")
            
            score = min(30, count * 3)
            
            return {
                'score': score,
                'max': 30,
                'value': count,
                'label': f"{count} analiz"
            }
        except Exception as e:
            logger.error(f"❌ Analiz sayısı hatası: {e}")
            return {'score': 0, 'max': 30, 'value': 0, 'label': '0 analiz'}
    
    def _score_verified_rules(self) -> Dict[str, Any]:
        """Doğrulanmış davranış sayısı (max 25)"""
        try:
            count = self.db.query(CompanyLearningMemory).filter(
                CompanyLearningMemory.user_id == self.user_id,
                CompanyLearningMemory.is_active == True,
                CompanyLearningMemory.is_verified == True
            ).count()
            
            logger.info(f"📊 Doğrulanmış kural sayısı: {count}")
            
            score = min(25, count * 2.5)
            
            return {
                'score': score,
                'max': 25,
                'value': count,
                'label': f"{count} doğrulanmış kural"
            }
        except Exception as e:
            logger.error(f"❌ Doğrulanmış kural sayısı hatası: {e}")
            return {'score': 0, 'max': 25, 'value': 0, 'label': '0 doğrulanmış kural'}
    
    def _score_data_quality(self) -> Dict[str, Any]:
        """Veri kalitesi bileşeni (max 20)"""
        try:
            from app.models import AnalysisDataset
            
            dataset = self.db.query(AnalysisDataset).filter(
                AnalysisDataset.user_id == self.user_id,
                AnalysisDataset.is_active == True
            ).order_by(AnalysisDataset.created_at.desc()).first()
            
            if not dataset:
                logger.info(f"📊 Veri kalitesi: Dataset yok")
                return {'score': 0, 'max': 20, 'value': 0, 'label': 'Veri yok'}
            
            score = 0
            
            data_points = dataset.data_points or 0
            if data_points > 10000:
                score += 10
            elif data_points > 5000:
                score += 7
            elif data_points > 1000:
                score += 4
            else:
                score += 2
            
            product_count = dataset.product_count or 0
            if product_count > 100:
                score += 5
            elif product_count > 50:
                score += 3
            elif product_count > 10:
                score += 2
            else:
                score += 1
            
            period_count = dataset.period_count or 0
            if period_count > 52:
                score += 5
            elif period_count > 26:
                score += 3
            elif period_count > 12:
                score += 2
            else:
                score += 1
            
            score = min(20, score)
            
            logger.info(f"📊 Veri kalitesi: {score}/20 (data_points={data_points}, product_count={product_count}, period_count={period_count})")
            
            return {
                'score': score,
                'max': 20,
                'value': score,
                'label': f"{data_points} veri noktası, {product_count} ürün"
            }
            
        except Exception as e:
            logger.error(f"❌ Veri kalitesi hatası: {e}")
            return {'score': 0, 'max': 20, 'value': 0, 'label': 'Veri kalitesi hesaplanamadı'}
    
    def _score_forecast_accuracy(self) -> Dict[str, Any]:
        """Forecast doğruluğu bileşeni (max 15)"""
        try:
            forecast = self.db.query(AnalysisResult).filter(
                AnalysisResult.user_id == self.user_id,
                AnalysisResult.result_type.like('%forecast%'),
                AnalysisResult.status == 'completed'
            ).order_by(AnalysisResult.created_at.desc()).first()
            
            if not forecast:
                logger.info(f"📊 Forecast doğruluğu: Forecast yok")
                return {'score': 0, 'max': 15, 'value': 0, 'label': 'Forecast yok'}
            
            data = forecast.data or {}
            results = data.get('results', [])
            
            if not results:
                return {'score': 0, 'max': 15, 'value': 0, 'label': 'Forecast sonucu yok'}
            
            rmse_values = []
            for r in results:
                rmse = r.get('model_rmse')
                if rmse and rmse < 999:
                    rmse_values.append(rmse)
            
            if not rmse_values:
                return {'score': 0, 'max': 15, 'value': 0, 'label': 'RMSE verisi yok'}
            
            avg_rmse = sum(rmse_values) / len(rmse_values)
            
            if avg_rmse < 20:
                score = 15
            elif avg_rmse < 30:
                score = 12
            elif avg_rmse < 40:
                score = 9
            elif avg_rmse < 50:
                score = 6
            elif avg_rmse < 75:
                score = 3
            else:
                score = 1
            
            logger.info(f"📊 Forecast doğruluğu: {score}/15 (avg_rmse={avg_rmse:.2f})")
            
            return {
                'score': score,
                'max': 15,
                'value': avg_rmse,
                'label': f"RMSE: {avg_rmse:.2f}"
            }
            
        except Exception as e:
            logger.error(f"❌ Forecast doğruluğu hatası: {e}")
            return {'score': 0, 'max': 15, 'value': 0, 'label': 'Forecast doğruluğu hesaplanamadı'}
    
    def _score_ai_confidence(self) -> Dict[str, Any]:
        """AI güven skoru bileşeni (max 10)"""
        try:
            results = self.db.query(AnalysisResult).filter(
                AnalysisResult.user_id == self.user_id,
                AnalysisResult.ai_status == 'completed',
                AnalysisResult.ai_summary.isnot(None)
            ).order_by(AnalysisResult.created_at.desc()).limit(5).all()
            
            if not results:
                logger.info(f"📊 AI güven: AI analizi yok")
                return {'score': 0, 'max': 10, 'value': 0, 'label': 'AI analizi yok'}
            
            confidences = []
            for r in results:
                ai_summary = r.ai_summary or {}
                conf = ai_summary.get('confidence', 0.5)
                if isinstance(conf, (int, float)):
                    confidences.append(conf)
            
            if not confidences:
                return {'score': 0, 'max': 10, 'value': 0, 'label': 'Güven verisi yok'}
            
            avg_confidence = sum(confidences) / len(confidences)
            score = int(avg_confidence * 10)
            score = min(10, max(0, score))
            
            logger.info(f"📊 AI güven: {score}/10 (avg_confidence={avg_confidence:.2f})")
            
            return {
                'score': score,
                'max': 10,
                'value': avg_confidence,
                'label': f"%{int(avg_confidence * 100)} güven"
            }
            
        except Exception as e:
            logger.error(f"❌ AI güven skoru hatası: {e}")
            return {'score': 0, 'max': 10, 'value': 0, 'label': 'AI güven skoru hesaplanamadı'}
    
    def _get_level(self, score: int) -> str:
        """Skora göre seviye belirler"""
        if score >= 80:
            return "Uzman"
        elif score >= 60:
            return "İleri"
        elif score >= 40:
            return "Orta"
        elif score >= 20:
            return "Başlangıç"
        else:
            return "Öğreniyor"