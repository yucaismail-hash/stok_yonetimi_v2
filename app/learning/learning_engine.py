# app/learning/learning_engine.py
"""
Learning Engine - DOCUMENT 05 - PART 01
Single entry point for all learning operations.
"""

from typing import Optional, Dict, Any, List  # ✅ EKLENDI: List
from uuid import uuid4
import logging

from sqlalchemy.orm import Session  # ✅ Zaten var, doğru

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.learning.company_learning import CompanyLearningEngine
from app.learning.pattern_intelligence import PatternIntelligenceEngine
from app.learning.decision_learning import DecisionLearningEngine
from app.learning.sector_intelligence import SectorIntelligenceEngine
from app.learning.knowledge_maturity import KnowledgeMaturityEngine
from app.learning.learning_trigger import LearningTrigger
from app.learning.learning_explainability import LearningExplainability


logger = logging.getLogger(__name__)


class LearningEngine:
    """
    Learning Engine - DOCUMENT 05
    
    Single entry point for all learning operations.
    Orchestrates all learning layers internally.
    
    Execution order:
    1. Company Learning
    2. Pattern Intelligence
    3. Decision Learning
    4. Sector Intelligence
    5. Knowledge Maturity
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.trigger = LearningTrigger(db)
        self.explainability = LearningExplainability(db)
        
        # Initialize learning engines
        self.company_learning = CompanyLearningEngine(db)
        self.pattern_intelligence = PatternIntelligenceEngine(db)
        self.decision_learning = DecisionLearningEngine(db)
        self.sector_intelligence = SectorIntelligenceEngine(db)
        self.knowledge_maturity = KnowledgeMaturityEngine(db)
    
    def learn(self, context: LearningContext) -> Dict[str, Any]:
        """
        Single entry point for learning.
        
        Args:
            context: LearningContext with all required information
        
        Returns:
            Learning result with all layers' outputs
        """
        # Generate learning cycle ID
        context.learning_cycle_id = str(uuid4())
        
        logger.info(f"🧠 Learning cycle started: {context.learning_cycle_id}")
        
        # 1. Check if learning should be triggered
        if not self.trigger.should_trigger(context):
            logger.info(f"⏭️ Learning not triggered for: {context.learning_cycle_id}")
            return {
                "learning_cycle_id": context.learning_cycle_id,
                "triggered": False,
                "reason": "Learning conditions not met",
            }
        
        # 2. Execute learning layers in order
        results = {
            "learning_cycle_id": context.learning_cycle_id,
            "triggered": True,
            "layers": {},
            "success": True,
            "errors": [],
        }
        
        try:
            # Layer 01: Company Learning
            logger.info("📚 Layer 01: Company Learning started")
            company_result = self.company_learning.learn(context)
            results["layers"]["company_learning"] = company_result
            logger.info(f"✅ Company Learning completed: {len(company_result.get('rules', []))} rules")
            
            # Layer 02: Pattern Intelligence
            logger.info("📊 Layer 02: Pattern Intelligence started")
            pattern_result = self.pattern_intelligence.learn(context)
            results["layers"]["pattern_intelligence"] = pattern_result
            logger.info(f"✅ Pattern Intelligence completed: {len(pattern_result.get('patterns', []))} patterns")
            
            # Layer 03: Decision Learning
            logger.info("🎯 Layer 03: Decision Learning started")
            decision_result = self.decision_learning.learn(context)
            results["layers"]["decision_learning"] = decision_result
            logger.info(f"✅ Decision Learning completed: {len(decision_result.get('decisions', []))} decisions")
            
            # Layer 04: Sector Intelligence (if enough data)
            logger.info("🏢 Layer 04: Sector Intelligence started")
            sector_result = self.sector_intelligence.learn(context)
            results["layers"]["sector_intelligence"] = sector_result
            logger.info(f"✅ Sector Intelligence completed")
            
            # Layer 05: Knowledge Maturity
            logger.info("📈 Layer 05: Knowledge Maturity started")
            maturity_result = self.knowledge_maturity.calculate(context)
            results["layers"]["knowledge_maturity"] = maturity_result
            logger.info(f"✅ Knowledge Maturity completed: {maturity_result.get('maturity_level', 'unknown')}")
            
            # 3. Explainability
            explanation = self.explainability.explain(context, results)
            results["explanation"] = explanation
            
            # 4. Commit all changes
            self.db.commit()
            
            logger.info(f"🎉 Learning cycle completed: {context.learning_cycle_id}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Learning cycle failed: {str(e)}")
            self.db.rollback()
            
            results["success"] = False
            results["errors"].append(str(e))
            
            return results
    
    def get_learning_history(self, company_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get learning history for a company."""
        # Placeholder - will be implemented with proper history tracking
        return []