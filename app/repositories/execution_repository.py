# app/repositories/execution_repository.py
"""
Execution Repository
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.execution import (
    AnalysisResult,
    ExecutionResult,
    ExecutionMetrics,
    ExecutionCache
)
from app.repositories.base import BaseRepository


class AnalysisResultRepository(BaseRepository[AnalysisResult]):
    """Repository for AnalysisResult entity."""

    def __init__(self, db: Session):
        super().__init__(db, AnalysisResult)

    def get_by_task_id(self, task_id: str) -> Optional[AnalysisResult]:
        """Get analysis result by task ID."""
        return self.db.query(AnalysisResult).filter(
            AnalysisResult.task_id == task_id,
            AnalysisResult.is_deleted == False
        ).first()

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AnalysisResult]:
        """Get analysis results by user."""
        return self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user_id,
            AnalysisResult.is_deleted == False
        ).offset(skip).limit(limit).all()

    def get_by_result_type(self, result_type: str, user_id: Optional[UUID] = None) -> List[AnalysisResult]:
        """Get analysis results by type."""
        query = self.db.query(AnalysisResult).filter(
            AnalysisResult.result_type == result_type,
            AnalysisResult.is_deleted == False
        )
        if user_id:
            query = query.filter(AnalysisResult.user_id == user_id)
        return query.all()

    def get_recent(self, user_id: UUID, limit: int = 10) -> List[AnalysisResult]:
        """Get recent analysis results."""
        return self.db.query(AnalysisResult).filter(
            AnalysisResult.user_id == user_id,
            AnalysisResult.is_deleted == False
        ).order_by(
            AnalysisResult.created_at.desc()
        ).limit(limit).all()


class ExecutionResultRepository(BaseRepository[ExecutionResult]):
    """Repository for ExecutionResult entity."""

    def __init__(self, db: Session):
        super().__init__(db, ExecutionResult)

    def get_by_workflow_id(self, workflow_id: str) -> Optional[ExecutionResult]:
        """Get execution result by workflow ID."""
        return self.db.query(ExecutionResult).filter(
            ExecutionResult.workflow_id == workflow_id,
            ExecutionResult.is_deleted == False
        ).first()

    def get_by_user(self, user_id: UUID) -> list:
        """Get execution results by user."""
        return self.db.query(ExecutionResult).filter(
            ExecutionResult.user_id == user_id,
            ExecutionResult.is_deleted == False
        ).all()

    def get_completed_by_company(self, company_id: UUID) -> list:
        """Get completed executions by company."""
        return self.db.query(ExecutionResult).filter(
            ExecutionResult.company_id == company_id,
            ExecutionResult.status == "completed",
            ExecutionResult.is_deleted == False
        ).all()


class ExecutionMetricsRepository(BaseRepository[ExecutionMetrics]):
    """Repository for ExecutionMetrics entity."""

    def __init__(self, db: Session):
        super().__init__(db, ExecutionMetrics)

    def get_by_execution(self, execution_id: UUID) -> Optional[ExecutionMetrics]:
        """Get metrics by execution ID."""
        return self.db.query(ExecutionMetrics).filter(
            ExecutionMetrics.execution_id == execution_id,
            ExecutionMetrics.is_deleted == False
        ).first()


class ExecutionCacheRepository(BaseRepository[ExecutionCache]):
    """Repository for ExecutionCache entity."""

    def __init__(self, db: Session):
        super().__init__(db, ExecutionCache)

    def get_by_dataset_and_sku(self, dataset_id: UUID, sku_code: str, result_type: str) -> Optional[ExecutionCache]:
        """Get cache by dataset, SKU and result type."""
        return self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id,
            ExecutionCache.sku_code == sku_code,
            ExecutionCache.result_type == result_type,
            ExecutionCache.is_valid == True,
            ExecutionCache.is_deleted == False
        ).first()

    def invalidate_by_dataset(self, dataset_id: UUID):
        """Invalidate all cache entries for a dataset."""
        self.db.query(ExecutionCache).filter(
            ExecutionCache.dataset_id == dataset_id
        ).update({"is_valid": False})

    def invalidate_by_algorithm(self, algorithm_version: str):
        """Invalidate cache entries by algorithm version."""
        self.db.query(ExecutionCache).filter(
            ExecutionCache.algorithm_version != algorithm_version
        ).update({"is_valid": False})