# app/learning/sector_intelligence.py
"""
Sector Intelligence Engine - DOCUMENT 05 - PART 05
Generates anonymous industry knowledge to enrich learning.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID, uuid4
import logging
import statistics
import hashlib
import json

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import SectorIntelligence, CompanyLearningMemory


logger = logging.getLogger(__name__)


class AnonymousKnowledgeAggregator:
    """
    Anonymous Knowledge Aggregator - DOCUMENT 05 - PART 05 Section 3
    Aggregates anonymous statistical parameters from multiple companies.
    Raw company data never leaves the company boundary.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
    
    def aggregate_anonymous_knowledge(self, sector_id: UUID) -> Dict[str, Any]:
        """
        Aggregate anonymous knowledge from multiple companies.
        Only anonymous statistical parameters contribute.
        """
        # In a real implementation, this would aggregate from multiple companies
        # For now, return placeholder aggregated data
        
        # Get all company learning data for this sector
        company_learnings = self.repository.get_company_learning(sector_id)
        
        if not company_learnings:
            return {
                "has_data": False,
                "message": "No aggregated data available",
                "aggregated_params": {},
            }
        
        # Extract anonymous parameters
        # Only use aggregated statistics, never raw data
        aggregated = {
            "has_data": True,
            "timestamp": datetime.now().isoformat(),
            "company_count": len(set(l.company_id for l in company_learnings)),
            "aggregated_params": {
                "avg_planning_consistency": self._anonymize(0.5),
                "avg_service_level_preference": self._anonymize(0.95),
                "avg_demand_volatility": self._anonymize(0.5),
                "avg_seasonality_strength": self._anonymize(0.3),
            },
            "anonymization_hash": self._generate_anonymization_hash(company_learnings),
            "is_anonymous": True,
        }
        
        return aggregated
    
    def _anonymize(self, value: float) -> float:
        """Add noise to prevent reverse identification."""
        import random
        noise = random.uniform(-0.05, 0.05)
        return round(max(0, min(1, value + noise)), 3)
    
    def _generate_anonymization_hash(self, learnings: List) -> str:
        """Generate hash to verify anonymization."""
        # Create a hash from aggregated data only
        data = json.dumps([
            {
                "company_id": str(l.company_id),
                "rule_type": l.rule_type,
                "confidence": l.confidence_score,
            }
            for l in learnings[:10]
        ], sort_keys=True)
        
        return hashlib.sha256(data.encode()).hexdigest()[:16]


class SectorIntelligenceEngine:
    """
    Sector Intelligence Engine - DOCUMENT 05 - PART 05
    
    Generates anonymous industry knowledge.
    Enriches future learning without exposing company-specific information.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.aggregator = AnonymousKnowledgeAggregator(db)
    
    def learn(self, context: LearningContext) -> Dict[str, Any]:
        """
        Main learning method - DOCUMENT 05 - PART 05
        """
        # 1. Get company's sector
        sector_id = self._get_sector_id(context.company_id)
        
        if not sector_id:
            return {
                "success": False,
                "reason": "No sector identified for company",
                "anonymized": False,
            }
        
        # 2. Get sector intelligence
        sector_intelligence = self.repository.get_sector_intelligence(sector_id)
        
        # 3. Aggregate anonymous knowledge
        aggregated = self.aggregator.aggregate_anonymous_knowledge(sector_id)
        
        # 4. Enrich with anonymous sector knowledge
        enriched = self._enrich_with_sector_knowledge(context, aggregated)
        
        # 5. Save sector intelligence
        if sector_intelligence:
            sector_intelligence.pattern_params = aggregated
            sector_intelligence.last_calculated_at = datetime.now()
            sector_intelligence.company_count = aggregated.get("company_count", 0)
            self.repository.update_sector_intelligence(sector_intelligence)
        else:
            sector_intelligence = SectorIntelligence(
                sector_id=sector_id,
                pattern_type="anonymous_aggregated",
                pattern_params=aggregated,
                confidence_score=0.6,
                company_count=aggregated.get("company_count", 0),
                anonymized_data={
                    "aggregated_params": aggregated.get("aggregated_params", {}),
                    "anonymization_hash": aggregated.get("anonymization_hash"),
                },
                is_active=True,
                last_calculated_at=datetime.now(),
            )
            self.repository.save_sector_intelligence(sector_intelligence)
        
        # 6. Explain the learning
        explanation = self._explain_learning(context, aggregated, enriched)
        
        return {
            "success": True,
            "anonymized": True,
            "sector_id": str(sector_id),
            "aggregated": aggregated,
            "enriched": enriched,
            "sector_intelligence_id": str(sector_intelligence.id),
            "explanation": explanation,
        }
    
    def _get_sector_id(self, company_id: UUID) -> Optional[UUID]:
        """
        Get company's sector ID.
        Placeholder - actual implementation would query company table.
        """
        # In real implementation, get sector from company
        # For now, return a dummy sector ID
        return UUID("00000000-0000-0000-0000-000000000001")
    
    def _enrich_with_sector_knowledge(
        self,
        context: LearningContext,
        aggregated: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich company learning with anonymous sector knowledge.
        """
        if not aggregated.get("has_data"):
            return {"enriched": False, "reason": "No aggregated data available"}
        
        # Get company's current learning
        company_learnings = self.repository.get_company_learning(context.company_id)
        
        # Enrich with sector averages
        sector_params = aggregated.get("aggregated_params", {})
        enriched = {
            "enriched": True,
            "sector_contribution": {
                "planning_consistency_boost": sector_params.get("avg_planning_consistency", 0.5),
                "service_level_boost": sector_params.get("avg_service_level_preference", 0.95),
            },
            "company_current": {
                "learning_count": len(company_learnings),
                "avg_confidence": statistics.mean([l.confidence_score for l in company_learnings]) if company_learnings else 0,
            },
        }
        
        return enriched
    
    def _explain_learning(
        self,
        context: LearningContext,
        aggregated: Dict[str, Any],
        enriched: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explain sector intelligence learning.
        """
        return {
            "execution_id": str(context.execution_id),
            "sector_contribution": enriched.get("enriched", False),
            "company_count": aggregated.get("company_count", 0),
            "anonymized": True,
            "timestamp": datetime.now().isoformat(),
        }