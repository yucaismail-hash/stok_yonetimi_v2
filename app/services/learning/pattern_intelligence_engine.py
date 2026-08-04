# app/services/learning/pattern_intelligence_engine.py
"""
Pattern Intelligence Engine
DOCUMENT 01 - Pattern Intelligence

Learns product and product-group behaviour using company data.
Depends on Company Learning.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from collections import defaultdict
import statistics

from sqlalchemy.orm import Session

from app.models.learning import PatternIntelligence, CompanyLearningMemory
from app.models.company import ProductGroup, UserMaterial

logger = logging.getLogger(__name__)


class PatternIntelligenceEngine:
    """
    Pattern Intelligence Motoru.
    
    Ürün ve ürün grubu bazında desen öğrenir.
    Company Learning'e bağımlıdır.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def learn_from_company_learning(
        self,
        user_id: int,
        company_learning: List[CompanyLearningMemory],
    ) -> List[PatternIntelligence]:
        """
        Company Learning sonuçlarından pattern öğren.
        """
        patterns = []
        
        # 1. Talep desenlerini grupla
        demand_patterns = [
            r for r in company_learning 
            if r.rule_type == "demand_pattern" and r.is_verified
        ]
        
        # 2. Ürün grubu bazında grupla
        grouped = defaultdict(list)
        for pattern in demand_patterns:
            sku = pattern.pattern_data.get("sku")
            if sku:
                # SKU'nun ürün grubunu bul
                material = self.db.query(UserMaterial).filter(
                    UserMaterial.user_id == user_id,
                    UserMaterial.code == sku
                ).first()
                
                if material and material.product_group_id:
                    grouped[material.product_group_id].append(pattern)
        
        # 3. Her grup için pattern oluştur
        for group_id, patterns_list in grouped.items():
            if len(patterns_list) < 3:
                continue
            
            # Desen tiplerini topla
            pattern_types = [p.pattern_data.get("pattern_type") for p in patterns_list]
            
            # En yaygın deseni bul
            most_common = max(set(pattern_types), key=pattern_types.count)
            avg_confidence = statistics.mean([p.confidence_score for p in patterns_list])
            
            # Pattern Intelligence oluştur
            pattern = PatternIntelligence(
                user_id=user_id,
                product_group_id=group_id,
                pattern_type=most_common,
                pattern_params={
                    "source_rules": [p.rule_id for p in patterns_list],
                    "confidence_avg": avg_confidence,
                    "sample_count": len(patterns_list),
                },
                confidence_score=avg_confidence,
                company_learning_id=patterns_list[0].id if patterns_list else None,
                is_active=True,
                last_calculated_at=datetime.now(),
            )
            
            self.db.add(pattern)
            patterns.append(pattern)
        
        self.db.commit()
        
        logger.info(f"✅ Pattern intelligence completed for user {user_id}: {len(patterns)} patterns")
        
        return patterns
    
    def get_product_pattern(self, user_id: int, product_group_id: int) -> Optional[PatternIntelligence]:
        """Ürün grubu pattern'ini getir."""
        return self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.product_group_id == product_group_id,
            PatternIntelligence.is_active == True
        ).first()
    
    def get_all_patterns(self, user_id: int) -> List[PatternIntelligence]:
        """Tüm pattern'leri getir."""
        return self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.is_active == True
        ).order_by(PatternIntelligence.confidence_score.desc()).all()
    
    def update_pattern(self, pattern_id: int, new_data: Dict[str, Any]) -> Optional[PatternIntelligence]:
        """Pattern'i güncelle."""
        pattern = self.db.query(PatternIntelligence).filter(
            PatternIntelligence.id == pattern_id
        ).first()
        
        if not pattern:
            return None
        
        if "pattern_type" in new_data:
            pattern.pattern_type = new_data["pattern_type"]
        
        if "pattern_params" in new_data:
            pattern.pattern_params = new_data["pattern_params"]
        
        if "confidence_score" in new_data:
            pattern.confidence_score = new_data["confidence_score"]
        
        pattern.last_calculated_at = datetime.now()
        self.db.commit()
        
        return pattern