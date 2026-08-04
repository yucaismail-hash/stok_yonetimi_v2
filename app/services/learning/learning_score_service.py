# app/services/learning/learning_score_service.py
"""
Learning Score Service
DOCUMENT 01 - Knowledge Maturity

Tracks learning maturity and scores.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from sqlalchemy.orm import Session

from app.models.learning import KnowledgeMaturity, CompanyLearningMemory, PatternIntelligence

logger = logging.getLogger(__name__)


class LearningScoreService:
    """
    Learning Score Servisi.
    
    - Company Learning seviyesi
    - Pattern Intelligence seviyesi
    - Sector Intelligence seviyesi
    - Genel olgunluk seviyesi
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_maturity(self, user_id: int) -> KnowledgeMaturity:
        """
        Kullanıcının öğrenme olgunluk seviyesini hesapla.
        """
        # 1. Company Learning maturity
        company_learning = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.user_id == user_id,
            CompanyLearningMemory.is_active == True
        ).all()
        
        company_maturity = self._calculate_company_maturity(company_learning)
        
        # 2. Pattern Intelligence maturity
        pattern_intelligence = self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.is_active == True
        ).all()
        
        pattern_maturity = self._calculate_pattern_maturity(pattern_intelligence)
        
        # 3. Sector Intelligence maturity
        sector_maturity = self._calculate_sector_maturity(user_id)
        
        # 4. Overall maturity
        overall = (company_maturity + pattern_maturity + sector_maturity) / 3
        
        # 5. Level
        level = self._get_maturity_level(overall)
        
        # 6. Kaydet
        maturity = self.db.query(KnowledgeMaturity).filter(
            KnowledgeMaturity.user_id == user_id
        ).first()
        
        if not maturity:
            maturity = KnowledgeMaturity(user_id=user_id)
        
        maturity.company_learning_maturity = company_maturity
        maturity.pattern_intelligence_maturity = pattern_maturity
        maturity.sector_intelligence_maturity = sector_maturity
        maturity.overall_maturity = overall
        maturity.maturity_level = level
        maturity.total_learning_records = len(company_learning)
        maturity.verified_patterns = len([p for p in pattern_intelligence if p.confidence_score > 0.8])
        maturity.calculated_at = datetime.now()
        
        self.db.add(maturity)
        self.db.commit()
        
        logger.info(f"✅ Learning maturity calculated for user {user_id}: {level} ({overall:.2f})")
        
        return maturity
    
    def _calculate_company_maturity(self, learning_records: list) -> float:
        """Company Learning olgunluğunu hesapla."""
        if not learning_records:
            return 0.0
        
        total_records = len(learning_records)
        verified = len([r for r in learning_records if r.is_verified])
        avg_confidence = sum(r.confidence_score for r in learning_records) / total_records
        
        # 0-100 arası skor
        # Kayıt sayısı: 10+ kayıt = 30 puan
        # Verified oranı: %50+ = 30 puan
        # Ortalama confidence: 0.7+ = 40 puan
        
        score = 0
        
        # Kayıt sayısı (max 30)
        if total_records >= 10:
            score += 30
        elif total_records >= 5:
            score += 20
        elif total_records >= 3:
            score += 10
        
        # Verified oranı (max 30)
        verified_ratio = verified / total_records if total_records > 0 else 0
        if verified_ratio >= 0.7:
            score += 30
        elif verified_ratio >= 0.5:
            score += 20
        elif verified_ratio >= 0.3:
            score += 10
        
        # Confidence (max 40)
        if avg_confidence >= 0.8:
            score += 40
        elif avg_confidence >= 0.6:
            score += 25
        elif avg_confidence >= 0.4:
            score += 10
        
        return min(100, score)
    
    def _calculate_pattern_maturity(self, pattern_records: list) -> float:
        """Pattern Intelligence olgunluğunu hesapla."""
        if not pattern_records:
            return 0.0
        
        total = len(pattern_records)
        high_confidence = len([p for p in pattern_records if p.confidence_score > 0.8])
        
        # 0-100 arası skor
        score = 0
        
        # Pattern sayısı (max 50)
        if total >= 5:
            score += 50
        elif total >= 3:
            score += 30
        elif total >= 1:
            score += 15
        
        # Yüksek confidence oranı (max 50)
        high_ratio = high_confidence / total if total > 0 else 0
        if high_ratio >= 0.8:
            score += 50
        elif high_ratio >= 0.5:
            score += 30
        elif high_ratio >= 0.3:
            score += 15
        
        return min(100, score)
    
    def _calculate_sector_maturity(self, user_id: int) -> float:
        """Sector Intelligence olgunluğunu hesapla."""
        # Kullanıcının sektörünü bul
        from app.models.company import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.company_name:
            return 0.0
        
        # Sektör intelligence var mı kontrol et
        sector_intelligence = self.db.query(SectorIntelligence).filter(
            SectorIntelligence.is_active == True
        ).all()
        
        if not sector_intelligence:
            return 0.0
        
        # Sektör intelligence kullanılabilir mi?
        # DOCUMENT 01: Sektör verileri anonim olduğu için herkes kullanabilir
        
        # Her şirket sektör intelligence'dan faydalanabilir
        # Başlangıç için 30 puan
        return 30.0
    
    def _get_maturity_level(self, score: float) -> str:
        """Olgunluk seviyesini belirle."""
        if score >= 80:
            return "expert"
        elif score >= 60:
            return "advanced"
        elif score >= 40:
            return "intermediate"
        elif score >= 20:
            return "beginner"
        else:
            return "novice"
    
    def get_maturity(self, user_id: int) -> Optional[KnowledgeMaturity]:
        """Kullanıcının olgunluk seviyesini getir."""
        return self.db.query(KnowledgeMaturity).filter(
            KnowledgeMaturity.user_id == user_id
        ).first()