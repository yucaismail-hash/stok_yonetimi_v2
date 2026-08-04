# app/repositories/__init__.py
"""
Repository Layer - Data access abstraction.
"""

from app.repositories.base import BaseRepository

from app.repositories.company_repository import CompanyRepository
from app.repositories.user_repository import UserRepository
from app.repositories.dataset_repository import DatasetRepository, AnalysisDatasetRepository
from app.repositories.execution_repository import (
    AnalysisResultRepository,
    ExecutionResultRepository,
    ExecutionMetricsRepository,
    ExecutionCacheRepository
)
from app.repositories.learning_repository import (
    CompanyLearningMemoryRepository,
    UserLearningDataRepository,
    PatternIntelligenceRepository,
    SectorIntelligenceRepository,
    KnowledgeMaturityRepository,
    CompanyAIMemoryRepository
)
from app.repositories.audit_repository import (
    AuditLogRepository,
    SecurityEventRepository
)

__all__ = [
    # Base
    "BaseRepository",
    # Company
    "CompanyRepository",
    "UserRepository",
    # Dataset
    "DatasetRepository",
    "AnalysisDatasetRepository",
    # Execution
    "AnalysisResultRepository",
    "ExecutionResultRepository",
    "ExecutionMetricsRepository",
    "ExecutionCacheRepository",
    # Learning
    "CompanyLearningMemoryRepository",
    "UserLearningDataRepository",
    "PatternIntelligenceRepository",
    "SectorIntelligenceRepository",
    "KnowledgeMaturityRepository",
    "CompanyAIMemoryRepository",
    # Audit
    "AuditLogRepository",
    "SecurityEventRepository",
]