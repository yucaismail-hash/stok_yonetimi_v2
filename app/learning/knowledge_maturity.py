# app/learning/knowledge_maturity.py
"""
Knowledge Maturity Engine - DOCUMENT 05 - PART 05
Evaluates learning maturity and overall learning health.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import UUID
import logging
import statistics

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import KnowledgeMaturity
from app.models.company import User, Sector


logger = logging.getLogger(__name__)


class KnowledgeMaturityEngine:
    """
    Knowledge Maturity Engine - DOCUMENT 05 - PART 05
    
    Evaluates how well the platform has learned.
    Does NOT evaluate forecast accuracy, financial success, or business performance.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
    
    def calculate(self, context: LearningContext) -> Dict[str, Any]:
        """
        Calculate knowledge maturity for a company.
        """
        # 1. Get existing maturity
        maturity = self.repository.get_knowledge_maturity(context.user_id)
        
        # 2. Calculate each dimension
        company_maturity = self._calculate_company_maturity(context)
        pattern_maturity = self._calculate_pattern_maturity(context)
        decision_maturity = self._calculate_decision_maturity(context)
        sector_contribution = self._calculate_sector_contribution(context)
        
        # 3. Calculate overall maturity
        overall = self._calculate_overall_maturity(
            company_maturity,
            pattern_maturity,
            decision_maturity,
            sector_contribution,
        )
        
        # 4. Determine maturity level
        maturity_level = self._determine_maturity_level(overall)
        
        # 5. Calculate overall learning health
        health = self._calculate_learning_health(
            maturity,
            company_maturity,
            pattern_maturity,
            decision_maturity,
        )
        
        # 6. Save or update
        if maturity:
            maturity.company_learning_maturity = company_maturity
            maturity.pattern_intelligence_maturity = pattern_maturity
            maturity.sector_intelligence_maturity = sector_contribution
            maturity.overall_maturity = overall
            maturity.maturity_level = maturity_level
            maturity.updated_at = datetime.now()
            self.repository.update_knowledge_maturity(maturity)
        else:
            maturity = KnowledgeMaturity(
                user_id=context.user_id,
                company_learning_maturity=company_maturity,
                pattern_intelligence_maturity=pattern_maturity,
                sector_intelligence_maturity=sector_contribution,
                overall_maturity=overall,
                maturity_level=maturity_level,
                total_learning_records=0,
                verified_patterns=0,
                usage_count=0,
            )
            self.repository.save_knowledge_maturity(maturity)
        
        # 7. Explain the evaluation
        explanation = self._explain_maturity(
            context,
            maturity,
            company_maturity,
            pattern_maturity,
            decision_maturity,
            sector_contribution,
            overall,
            health,
        )
        
        return {
            "maturity_level": maturity_level,
            "company_maturity": company_maturity,
            "pattern_maturity": pattern_maturity,
            "decision_maturity": decision_maturity,
            "sector_contribution": sector_contribution,
            "overall_maturity": overall,
            "overall_health": health,
            "explanation": explanation,
        }
    
    def _calculate_company_maturity(self, context: LearningContext) -> float:
        """
        Calculate Company Maturity - DOCUMENT 05 - PART 05 Section 6
        """
        # Get company learning data
        learnings = self.repository.get_company_learning(context.company_id)
        
        if not learnings:
            return 0.0
        
        # Factors:
        # 1. Number of learning records (max 30)
        record_score = min(30, len(learnings) * 3)
        
        # 2. Average confidence (max 40)
        avg_confidence = statistics.mean([l.confidence_score for l in learnings])
        confidence_score = avg_confidence * 40
        
        # 3. Verified ratio (max 30)
        verified = len([l for l in learnings if l.is_verified])
        verified_ratio = verified / len(learnings) if learnings else 0
        verified_score = verified_ratio * 30
        
        total = record_score + confidence_score + verified_score
        return round(min(100, total), 2)
    
    def _calculate_pattern_maturity(self, context: LearningContext) -> float:
        """
        Calculate Pattern Maturity - DOCUMENT 05 - PART 05 Section 6
        """
        # Get pattern intelligence
        patterns = self.repository.get_pattern_intelligence(context.user_id)
        
        if not patterns:
            return 0.0
        
        # Factors:
        # 1. Number of patterns (max 50)
        pattern_score = min(50, len(patterns) * 5)
        
        # 2. Average confidence (max 50)
        avg_confidence = statistics.mean([p.confidence_score for p in patterns])
        confidence_score = avg_confidence * 50
        
        total = pattern_score + confidence_score
        return round(min(100, total), 2)
    
    def _calculate_decision_maturity(self, context: LearningContext) -> float:
        """
        Calculate Decision Maturity - DOCUMENT 05 - PART 05 Section 6
        """
        # Get AI memory (decisions)
        decisions = self.repository.get_company_ai_memory(context.user_id)
        
        if not decisions:
            return 0.0
        
        # Factors:
        # 1. Number of decisions (max 40)
        decision_score = min(40, len(decisions) * 4)
        
        # 2. Feedback quality (max 30)
        feedback_scores = [
            d.confidence_after - d.confidence_before
            for d in decisions
            if d.confidence_after and d.confidence_before
        ]
        avg_improvement = statistics.mean(feedback_scores) if feedback_scores else 0
        feedback_score = min(30, max(0, avg_improvement * 50))
        
        # 3. Outcome success (max 30)
        successful = len([d for d in decisions if d.outcome_success is True])
        success_ratio = successful / len(decisions) if decisions else 0
        success_score = success_ratio * 30
        
        total = decision_score + feedback_score + success_score
        return round(min(100, total), 2)
    
    def _calculate_sector_contribution(self, context: LearningContext) -> float:
        """
        Calculate Sector Contribution - DOCUMENT 05 - PART 05 Section 6
        """
        # Get sector intelligence
        sector_id = self._get_sector_id(context.company_id)
        if sector_id:
            sector_intelligence = self.repository.get_sector_intelligence(sector_id)
            if sector_intelligence:
                # 50% base + 50% from sector data
                base = 50
                sector_score = sector_intelligence.confidence_score * 50
                return round(base + sector_score, 2)
        
        return 20.0  # Default low sector contribution
    
    def _get_sector_id(self, company_id: UUID) -> Optional[UUID]:
        """Get company's sector ID."""
        # Placeholder - actual implementation would query company
        return UUID("00000000-0000-0000-0000-000000000001")
    
    def _calculate_overall_maturity(
        self,
        company: float,
        pattern: float,
        decision: float,
        sector: float,
    ) -> float:
        """
        Calculate Overall Maturity - DOCUMENT 05 - PART 05 Section 8
        """
        # Weighted average
        weights = {
            "company": 0.35,
            "pattern": 0.30,
            "decision": 0.25,
            "sector": 0.10,
        }
        
        total = (
            company * weights["company"] +
            pattern * weights["pattern"] +
            decision * weights["decision"] +
            sector * weights["sector"]
        )
        
        return round(total, 2)
    
    def _determine_maturity_level(self, score: float) -> str:
        """
        Determine maturity level - DOCUMENT 05 - PART 05 Section 7
        """
        if score >= 85:
            return "expert"
        elif score >= 70:
            return "mature"
        elif score >= 50:
            return "developing"
        elif score >= 30:
            return "learning"
        else:
            return "initial"
    
    def _calculate_learning_health(
        self,
        maturity: Optional[KnowledgeMaturity],
        company: float,
        pattern: float,
        decision: float,
    ) -> Dict[str, Any]:
        """
        Calculate Overall Learning Health - DOCUMENT 05 - PART 05 Section 8
        """
        # Health components
        components = {
            "learning_completeness": self._calculate_completeness(maturity),
            "knowledge_stability": self._calculate_stability(maturity),
            "learning_consistency": self._calculate_consistency(company, pattern, decision),
            "knowledge_evolution": self._calculate_evolution(maturity),
        }
        
        # Overall health score
        health_score = sum(components.values()) / 4
        
        return {
            "score": round(health_score, 2),
            "components": components,
            "status": "healthy" if health_score >= 60 else "needs_attention",
        }
    
    def _calculate_completeness(self, maturity: Optional[KnowledgeMaturity]) -> float:
        """Calculate learning completeness."""
        if not maturity:
            return 20.0
        
        # Total learning records
        records = maturity.total_learning_records or 0
        return min(100, records * 2 + 20)
    
    def _calculate_stability(self, maturity: Optional[KnowledgeMaturity]) -> float:
        """Calculate knowledge stability."""
        if not maturity:
            return 20.0
        
        # Verified patterns ratio
        verified = maturity.verified_patterns or 0
        records = maturity.total_learning_records or 1
        return min(100, (verified / records) * 100)
    
    def _calculate_consistency(self, company: float, pattern: float, decision: float) -> float:
        """Calculate learning consistency."""
        # Low variance indicates consistency
        values = [company, pattern, decision]
        if all(v == 0 for v in values):
            return 20.0
        
        variance = statistics.variance(values) if len(values) > 1 else 0
        consistency = 100 - min(100, variance * 5)
        return max(0, consistency)
    
    def _calculate_evolution(self, maturity: Optional[KnowledgeMaturity]) -> float:
        """Calculate knowledge evolution."""
        if not maturity:
            return 20.0
        
        # Usage count indicates active learning
        usage = maturity.usage_count or 0
        return min(100, usage * 5 + 20)
    
    def _explain_maturity(
        self,
        context: LearningContext,
        maturity: KnowledgeMaturity,
        company: float,
        pattern: float,
        decision: float,
        sector: float,
        overall: float,
        health: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Explain maturity evaluation - DOCUMENT 05 - PART 05 Section 10
        """
        return {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "maturity_level": self._determine_maturity_level(overall),
            "company_maturity": company,
            "pattern_maturity": pattern,
            "decision_maturity": decision,
            "sector_contribution": sector,
            "overall_maturity": overall,
            "overall_health": health,
            "improvement_areas": self._identify_improvements(company, pattern, decision, sector),
            "timestamp": datetime.now().isoformat(),
        }
    
    def _identify_improvements(
        self,
        company: float,
        pattern: float,
        decision: float,
        sector: float,
    ) -> List[str]:
        """Identify improvement areas."""
        improvements = []
        
        if company < 40:
            improvements.append("Increase company learning data")
        if pattern < 40:
            improvements.append("Improve pattern intelligence coverage")
        if decision < 40:
            improvements.append("Collect more decision feedback")
        if sector < 30:
            improvements.append("Contribute to sector intelligence")
        
        return improvements if improvements else ["All dimensions are developing well"]