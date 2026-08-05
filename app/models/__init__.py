# app/models/__init__.py
"""
Models Package - All database models organized by domain.
Follows DOCUMENT 03 - Database Architecture Specification.
DOCUMENT 06A Integration: AIArtifact model imported.
"""

# Base
from app.models.base import BaseModel

# Company
from app.models.company import (
    Company,
    User,
    Sector,
    ProductGroup,
    Supplier,
    MaterialSupplier,
    UserMaterial,
)

# Dataset
from app.models.dataset import (
    AnalysisDataset,
    Dataset,
    DatasetState,
    DatasetOperationType,
    DatasetVersion,
    DatasetEvent,
    DatasetValidationResult,
    DatasetDiffResult,
)

# Execution
from app.models.execution import (
    AnalysisResult,
    ExecutionResult,
    ExecutionMetrics,
    ExecutionStageMetrics,
    ExecutionResourceMetrics,
    ExecutionCache,
)

# Workflow
from app.models.workflow import (
    WorkflowExecution,
    WorkflowTask,
)

# Learning
from app.models.learning import (
    CompanyLearningMemory,
    UserLearningData,
    PatternIntelligence,
    SectorIntelligence,
    KnowledgeMaturity,
    CompanyAIMemory,
)

# Security
from app.models.security import (
    CompanyEncryptionKey,
)

# Analytics
from app.models.analytics import (
    ForecastResult,
    SafetyStockResult,
    SupplierResult,
    BacktestResult,
    SimulationResult,
)

# External
from app.models.external import ExternalCache

# API / Credit
from app.models.api import (
    TokenCost,
    TokenHistory,
    CreditPackage,
    CreditTransaction,
    UserTokenTransaction,
    Notification,
    SupportTicket,
    UploadedData,
    AnalysisInput,
    AnalysisBatchResult,
    AnalysisMaterialSummary,
    NormalizationRule,
    ProcessingTransaction,
    ProcessingScoreRange,
    EndpointProfile,
    ValidationRule,
    AnalysisImpactRule,
    ValidationResult,
)

# Audit
from app.models.audit import (
    AuditLog,
    SecurityEvent,
)

# System
from app.models.system import (
    AlgorithmVersion,
    FeatureFlag,
    SystemSetting,
)

# DOCUMENT 06A - AI Artifact
from app.models.artifact import AIArtifact


__all__ = [
    # Audit
    "AuditLog",
    "SecurityEvent",
    # Base
    "BaseModel",
    # Company
    "Company",
    "User",
    "Sector",
    "ProductGroup",
    "Supplier",
    "MaterialSupplier",
    "UserMaterial",
    # Dataset
    "AnalysisDataset",
    "Dataset",
    "DatasetState",
    "DatasetOperationType",
    "DatasetVersion",
    "DatasetEvent",
    "DatasetValidationResult",
    "DatasetDiffResult",
    # Execution
    "AnalysisResult",
    "ExecutionResult",
    "ExecutionMetrics",
    "ExecutionStageMetrics",
    "ExecutionResourceMetrics",
    "ExecutionCache",
    # System
    "AlgorithmVersion",
    "FeatureFlag",
    "SystemSetting",
    # Workflow
    "WorkflowExecution",
    "WorkflowTask",
    # Learning
    "CompanyLearningMemory",
    "UserLearningData",
    "PatternIntelligence",
    "SectorIntelligence",
    "KnowledgeMaturity",
    "CompanyAIMemory",
    # Security
    "CompanyEncryptionKey",
    # Analytics
    "ForecastResult",
    "SafetyStockResult",
    "SupplierResult",
    "BacktestResult",
    "SimulationResult",
    # External
    "ExternalCache",
    # API
    "TokenCost",
    "TokenHistory",
    "CreditPackage",
    "CreditTransaction",
    "UserTokenTransaction",
    "Notification",
    "SupportTicket",
    "UploadedData",
    "AnalysisInput",
    "AnalysisBatchResult",
    "AnalysisMaterialSummary",
    "NormalizationRule",
    "ProcessingTransaction",
    "ProcessingScoreRange",
    "EndpointProfile",
    "ValidationRule",
    "AnalysisImpactRule",
    "ValidationResult",
    # DOCUMENT 06A
    "AIArtifact",
]