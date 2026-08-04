# app/learning/knowledge_repository.py
"""
Knowledge Repository - DOCUMENT 05 - PART 01
All persistence operations for the Learning Engine.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.learning import (
    CompanyLearningMemory,
    UserLearningData,
    PatternIntelligence,
    SectorIntelligence,
    KnowledgeMaturity,
    CompanyAIMemory,
)
from app.models.company import Company, User
from app.repositories.base import BaseRepository


class KnowledgeRepository:
    """
    Knowledge Repository - DOCUMENT 05
    
    Provides all persistence operations required by the Learning Engine.
    Learning modules do NOT access ORM models directly.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ============================================
    # COMPANY LEARNING
    # ============================================
    
    def get_company_learning(self, company_id: UUID, rule_type: Optional[str] = None) -> List[CompanyLearningMemory]:
        """Get company learning memory."""
        query = self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.company_id == company_id,
            CompanyLearningMemory.is_deleted == False
        )
        if rule_type:
            query = query.filter(CompanyLearningMemory.rule_type == rule_type)
        return query.all()
    
    def get_company_learning_by_rule_id(self, company_id: UUID, rule_id: str) -> Optional[CompanyLearningMemory]:
        """Get company learning by rule ID."""
        return self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.company_id == company_id,
            CompanyLearningMemory.rule_id == rule_id,
            CompanyLearningMemory.is_deleted == False
        ).first()
    
    def save_company_learning(self, learning: CompanyLearningMemory) -> CompanyLearningMemory:
        """Save company learning."""
        self.db.add(learning)
        self.db.flush()
        return learning
    
    def update_company_learning(self, learning: CompanyLearningMemory) -> CompanyLearningMemory:
        """Update company learning."""
        learning.updated_at = datetime.now()
        self.db.flush()
        return learning
    
    # ============================================
    # USER LEARNING DATA
    # ============================================
    
    def get_user_learning(self, user_id: UUID, learning_key: Optional[str] = None) -> List[UserLearningData]:
        """Get user learning data."""
        query = self.db.query(UserLearningData).filter(
            UserLearningData.user_id == user_id,
            UserLearningData.is_deleted == False
        )
        if learning_key:
            query = query.filter(UserLearningData.learning_key == learning_key)
        return query.all()
    
    def get_user_learning_by_key(self, learning_key: str) -> Optional[UserLearningData]:
        """Get user learning by learning key."""
        return self.db.query(UserLearningData).filter(
            UserLearningData.learning_key == learning_key,
            UserLearningData.is_deleted == False
        ).first()
    
    def save_user_learning(self, learning: UserLearningData) -> UserLearningData:
        """Save user learning."""
        self.db.add(learning)
        self.db.flush()
        return learning
    
    def update_user_learning(self, learning: UserLearningData) -> UserLearningData:
        """Update user learning."""
        learning.updated_at = datetime.now()
        self.db.flush()
        return learning
    
    # ============================================
    # PATTERN INTELLIGENCE
    # ============================================
    
    def get_pattern_intelligence(self, user_id: UUID, product_group_id: Optional[UUID] = None) -> List[PatternIntelligence]:
        """Get pattern intelligence."""
        query = self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.is_deleted == False
        )
        if product_group_id:
            query = query.filter(PatternIntelligence.product_group_id == product_group_id)
        return query.all()
    
    def get_pattern_intelligence_by_group(self, user_id: UUID, product_group_id: UUID) -> Optional[PatternIntelligence]:
        """Get pattern intelligence by product group."""
        return self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.product_group_id == product_group_id,
            PatternIntelligence.is_deleted == False
        ).first()
    
    def save_pattern_intelligence(self, intelligence: PatternIntelligence) -> PatternIntelligence:
        """Save pattern intelligence."""
        self.db.add(intelligence)
        self.db.flush()
        return intelligence
    
    def update_pattern_intelligence(self, intelligence: PatternIntelligence) -> PatternIntelligence:
        """Update pattern intelligence."""
        intelligence.updated_at = datetime.now()
        self.db.flush()
        return intelligence
    
    # ============================================
    # SECTOR INTELLIGENCE
    # ============================================
    
    def get_sector_intelligence(self, sector_id: UUID) -> Optional[SectorIntelligence]:
        """Get sector intelligence."""
        return self.db.query(SectorIntelligence).filter(
            SectorIntelligence.sector_id == sector_id,
            SectorIntelligence.is_deleted == False
        ).first()
    
    def get_all_sector_intelligence(self) -> List[SectorIntelligence]:
        """Get all sector intelligence."""
        return self.db.query(SectorIntelligence).filter(
            SectorIntelligence.is_deleted == False
        ).all()
    
    def save_sector_intelligence(self, intelligence: SectorIntelligence) -> SectorIntelligence:
        """Save sector intelligence."""
        self.db.add(intelligence)
        self.db.flush()
        return intelligence
    
    def update_sector_intelligence(self, intelligence: SectorIntelligence) -> SectorIntelligence:
        """Update sector intelligence."""
        intelligence.updated_at = datetime.now()
        self.db.flush()
        return intelligence
    
    # ============================================
    # KNOWLEDGE MATURITY
    # ============================================
    
    def get_knowledge_maturity(self, user_id: UUID) -> Optional[KnowledgeMaturity]:
        """Get knowledge maturity."""
        return self.db.query(KnowledgeMaturity).filter(
            KnowledgeMaturity.user_id == user_id,
            KnowledgeMaturity.is_deleted == False
        ).first()
    
    def save_knowledge_maturity(self, maturity: KnowledgeMaturity) -> KnowledgeMaturity:
        """Save knowledge maturity."""
        self.db.add(maturity)
        self.db.flush()
        return maturity
    
    def update_knowledge_maturity(self, maturity: KnowledgeMaturity) -> KnowledgeMaturity:
        """Update knowledge maturity."""
        maturity.updated_at = datetime.now()
        self.db.flush()
        return maturity
    
    # ============================================
    # COMPANY AI MEMORY
    # ============================================
    
    def get_company_ai_memory(self, user_id: UUID, decision_type: Optional[str] = None) -> List[CompanyAIMemory]:
        """Get company AI memory."""
        query = self.db.query(CompanyAIMemory).filter(
            CompanyAIMemory.user_id == user_id,
            CompanyAIMemory.is_deleted == False
        )
        if decision_type:
            query = query.filter(CompanyAIMemory.decision_type == decision_type)
        return query.all()
    
    def save_company_ai_memory(self, memory: CompanyAIMemory) -> CompanyAIMemory:
        """Save company AI memory."""
        self.db.add(memory)
        self.db.flush()
        return memory
    
    def update_company_ai_memory(self, memory: CompanyAIMemory) -> CompanyAIMemory:
        """Update company AI memory."""
        memory.updated_at = datetime.now()
        self.db.flush()
        return memory