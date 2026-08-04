# app/learning/__init__.py
"""
Learning Engine - DOCUMENT 05
"""

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.learning.learning_engine import LearningEngine
from app.learning.learning_trigger import LearningTrigger
from app.learning.learning_explainability import LearningExplainability

from app.learning.company_learning import CompanyLearningEngine
from app.learning.pattern_intelligence import PatternIntelligenceEngine
from app.learning.decision_learning import DecisionLearningEngine
from app.learning.sector_intelligence import SectorIntelligenceEngine
from app.learning.knowledge_maturity import KnowledgeMaturityEngine

from app.learning.knowledge_center import (
    HistoricalCoverageAnalyzer,
    MissingWeekDetector,
    OptionalDatasetAnalyzer,
    KnowledgeCompletenessCalculator,
    KnowledgeGuidanceService,
    KnowledgeUpdateService,
    KnowledgeExplainability as KnowledgeCenterExplainability,
)

__all__ = [
    # Core
    "LearningContext",
    "KnowledgeRepository",
    "LearningEngine",
    "LearningTrigger",
    "LearningExplainability",
    # Learning Layers
    "CompanyLearningEngine",
    "PatternIntelligenceEngine",
    "DecisionLearningEngine",
    "SectorIntelligenceEngine",
    "KnowledgeMaturityEngine",
    # Knowledge Center
    "HistoricalCoverageAnalyzer",
    "MissingWeekDetector",
    "OptionalDatasetAnalyzer",
    "KnowledgeCompletenessCalculator",
    "KnowledgeGuidanceService",
    "KnowledgeUpdateService",
    "KnowledgeCenterExplainability",
]