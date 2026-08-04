# app/repositories/learning_repository.py
"""
Learning Repository
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.learning import (
    CompanyLearningMemory,
    UserLearningData,
    PatternIntelligence,
    SectorIntelligence,
    KnowledgeMaturity,
    CompanyAIMemory
)
from app.repositories.base import BaseRepository


class CompanyLearningMemoryRepository(BaseRepository[CompanyLearningMemory]):
    """Repository for CompanyLearningMemory entity."""

    def __init__(self, db: Session):
        super().__init__(db, CompanyLearningMemory)

    def get_by_company(self, company_id: UUID) -> List[CompanyLearningMemory]:
        """Get all learning memories for a company."""
        return self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.company_id == company_id,
            CompanyLearningMemory.is_deleted == False
        ).all()

    def get_by_rule_type(self, company_id: UUID, rule_type: str) -> List[CompanyLearningMemory]:
        """Get learning memories by rule type."""
        return self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.company_id == company_id,
            CompanyLearningMemory.rule_type == rule_type,
            CompanyLearningMemory.is_deleted == False
        ).all()

    def get_verified(self, company_id: UUID) -> List[CompanyLearningMemory]:
        """Get verified learning memories."""
        return self.db.query(CompanyLearningMemory).filter(
            CompanyLearningMemory.company_id == company_id,
            CompanyLearningMemory.is_verified == True,
            CompanyLearningMemory.is_deleted == False
        ).all()


class UserLearningDataRepository(BaseRepository[UserLearningData]):
    """Repository for UserLearningData entity."""

    def __init__(self, db: Session):
        super().__init__(db, UserLearningData)

    def get_by_user(self, user_id: UUID) -> List[UserLearningData]:
        """Get learning data for a user."""
        return self.db.query(UserLearningData).filter(
            UserLearningData.user_id == user_id,
            UserLearningData.is_deleted == False
        ).all()

    def get_by_learning_key(self, learning_key: str) -> Optional[UserLearningData]:
        """Get learning data by learning key."""
        return self.db.query(UserLearningData).filter(
            UserLearningData.learning_key == learning_key,
            UserLearningData.is_deleted == False
        ).first()


class PatternIntelligenceRepository(BaseRepository[PatternIntelligence]):
    """Repository for PatternIntelligence entity."""

    def __init__(self, db: Session):
        super().__init__(db, PatternIntelligence)

    def get_by_user(self, user_id: UUID) -> List[PatternIntelligence]:
        """Get pattern intelligence for a user."""
        return self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.is_deleted == False
        ).all()

    def get_by_product_group(self, user_id: UUID, product_group_id: UUID) -> Optional[PatternIntelligence]:
        """Get pattern intelligence by product group."""
        return self.db.query(PatternIntelligence).filter(
            PatternIntelligence.user_id == user_id,
            PatternIntelligence.product_group_id == product_group_id,
            PatternIntelligence.is_deleted == False
        ).first()


class SectorIntelligenceRepository(BaseRepository[SectorIntelligence]):
    """Repository for SectorIntelligence entity."""

    def __init__(self, db: Session):
        super().__init__(db, SectorIntelligence)

    def get_by_sector(self, sector_id: UUID) -> Optional[SectorIntelligence]:
        """Get sector intelligence by sector ID."""
        return self.db.query(SectorIntelligence).filter(
            SectorIntelligence.sector_id == sector_id,
            SectorIntelligence.is_deleted == False
        ).first()


class KnowledgeMaturityRepository(BaseRepository[KnowledgeMaturity]):
    """Repository for KnowledgeMaturity entity."""

    def __init__(self, db: Session):
        super().__init__(db, KnowledgeMaturity)

    def get_by_user(self, user_id: UUID) -> Optional[KnowledgeMaturity]:
        """Get knowledge maturity by user."""
        return self.db.query(KnowledgeMaturity).filter(
            KnowledgeMaturity.user_id == user_id,
            KnowledgeMaturity.is_deleted == False
        ).first()


class CompanyAIMemoryRepository(BaseRepository[CompanyAIMemory]):
    """Repository for CompanyAIMemory entity."""

    def __init__(self, db: Session):
        super().__init__(db, CompanyAIMemory)

    def get_by_user(self, user_id: UUID) -> List[CompanyAIMemory]:
        """Get AI memory for a user."""
        return self.db.query(CompanyAIMemory).filter(
            CompanyAIMemory.user_id == user_id,
            CompanyAIMemory.is_deleted == False
        ).all()

    def get_by_decision_type(self, user_id: UUID, decision_type: str) -> List[CompanyAIMemory]:
        """Get AI memory by decision type."""
        return self.db.query(CompanyAIMemory).filter(
            CompanyAIMemory.user_id == user_id,
            CompanyAIMemory.decision_type == decision_type,
            CompanyAIMemory.is_deleted == False
        ).all()