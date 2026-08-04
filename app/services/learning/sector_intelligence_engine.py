# app/services/learning/sector_intelligence_engine.py
"""
Sector Intelligence Engine
DOCUMENT 01 - Sector Intelligence

Learns anonymous sector-level behavioural patterns.
Raw company data MUST NEVER be shared.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import hashlib
import json
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.learning import SectorIntelligence
from app.models.company import Sector, ProductGroup

logger = logging.getLogger(__name__)


class SectorIntelligenceEngine:
    """
    Sector Intelligence Motoru.
    
    Anonim sektör seviyesinde davranış kalıpları öğrenir.
    Ham veri asla paylaşılmaz.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def anonymize_and_learn(
        self,
        sector_id: int,
        company_patterns: List[Dict[str, Any]],
        company_count: int,
    ) -> Optional[SectorIntelligence]:
        """
        Anonimleştirilmiş verilerden sektör öğrenmesi yap.
        """
        if len(company_patterns) < 3:
            logger.warning(f"Not enough company patterns for sector {sector_id}")
            return None
        
        # 1. Anonimleştir
        anonymized = self._anonymize_patterns(company_patterns)
        
        # 2. Sektör desenini hesapla
        sector_pattern = self._calculate_sector_pattern(anonymized)
        
        # 3. Kaydet
        intelligence = SectorIntelligence(
            sector_id=sector_id,
            pattern_type=sector_pattern.get("type", "mixed"),
            pattern_params=sector_pattern.get("params", {}),
            confidence_score=sector_pattern.get("confidence", 0.5),
            company_count=company_count,
            anonymized_data={
                "aggregated_factors": sector_pattern.get("aggregated_factors", {}),
                "common_patterns": sector_pattern.get("common_patterns", []),
                "anonymized_hash": self._anonymize_hash(company_patterns),
            },
            is_active=True,
            last_calculated_at=datetime.now(),
        )
        
        self.db.add(intelligence)
        self.db.commit()
        
        logger.info(f"✅ Sector intelligence updated for sector {sector_id}")
        
        return intelligence
    
    def _anonymize_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Verileri anonimleştir."""
        anonymized = []
        
        for pattern in patterns:
            # Sadece aggregate verileri tut
            anon = {
                "pattern_type": pattern.get("type", "unknown"),
                "confidence": pattern.get("confidence", 0.5),
                "seasonal_factors": pattern.get("seasonal_factors", {}),
                "trend": pattern.get("trend", "none"),
                "volatility": pattern.get("volatility", 0),
            }
            anonymized.append(anon)
        
        return anonymized
    
    def _calculate_sector_pattern(self, anonymized: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sektör desenini hesapla."""
        if not anonymized:
            return {"type": "unknown", "confidence": 0}
        
        # Desen tiplerini say
        pattern_types = [p.get("pattern_type", "unknown") for p in anonymized]
        type_counts = defaultdict(int)
        for pt in pattern_types:
            type_counts[pt] += 1
        
        # En yaygın desen
        most_common = max(type_counts.items(), key=lambda x: x[1])
        
        # Ortalama confidence
        avg_confidence = sum(p.get("confidence", 0) for p in anonymized) / len(anonymized)
        
        # Aggregate seasonal factors
        seasonal_factors = {}
        for p in anonymized:
            for factor, value in p.get("seasonal_factors", {}).items():
                if factor not in seasonal_factors:
                    seasonal_factors[factor] = []
                seasonal_factors[factor].append(value)
        
        # Ortalama seasonal factors
        avg_factors = {}
        for factor, values in seasonal_factors.items():
            avg_factors[factor] = sum(values) / len(values)
        
        return {
            "type": most_common[0],
            "confidence": min(1.0, avg_confidence + 0.1),  # Sektör verisi daha güvenilir
            "aggregated_factors": avg_factors,
            "common_patterns": [pt for pt, count in type_counts.items() if count > 1],
            "sample_size": len(anonymized),
        }
    
    def _anonymize_hash(self, patterns: List[Dict[str, Any]]) -> str:
        """Anonim veri hash'i."""
        hash_data = json.dumps([
            p.get("type", "") for p in patterns
        ], sort_keys=True)
        return hashlib.sha256(hash_data.encode()).hexdigest()[:16]
    
    def get_sector_intelligence(self, sector_id: int) -> Optional[SectorIntelligence]:
        """Sektör intelligence'ını getir."""
        return self.db.query(SectorIntelligence).filter(
            SectorIntelligence.sector_id == sector_id,
            SectorIntelligence.is_active == True
        ).first()
    
    def get_all_sector_intelligence(self) -> List[SectorIntelligence]:
        """Tüm sektör intelligence'larını getir."""
        return self.db.query(SectorIntelligence).filter(
            SectorIntelligence.is_active == True
        ).order_by(SectorIntelligence.confidence_score.desc()).all()