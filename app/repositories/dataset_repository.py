# app/repositories/dataset_repository.py
"""
Dataset Repository
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetVersion, AnalysisDataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository[Dataset]):
    """Repository for Dataset entity."""

    def __init__(self, db: Session):
        super().__init__(db, Dataset)

    def get_by_hash(self, dataset_hash: str) -> Optional[Dataset]:
        """Get dataset by hash."""
        return self.db.query(Dataset).filter(
            Dataset.dataset_hash == dataset_hash,
            Dataset.is_deleted == False
        ).first()

    def get_by_user(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """Get datasets by user."""
        return self.db.query(Dataset).filter(
            Dataset.user_id == user_id,
            Dataset.is_deleted == False
        ).offset(skip).limit(limit).all()

    def get_active_by_company(self, company_id: UUID) -> Optional[Dataset]:
        """Get active dataset by company."""
        return self.db.query(Dataset).filter(
            Dataset.company_id == company_id,
            Dataset.is_active == True,
            Dataset.is_deleted == False
        ).first()

    def get_versions(self, dataset_id: UUID) -> List[DatasetVersion]:
        """Get all versions of a dataset."""
        dataset = self.get_by_id(dataset_id)
        if dataset:
            return dataset.versions
        return []

    def get_latest_version(self, dataset_id: UUID) -> Optional[DatasetVersion]:
        """Get latest version of a dataset."""
        versions = self.get_versions(dataset_id)
        if versions:
            return max(versions, key=lambda v: v.version_number)
        return None


class AnalysisDatasetRepository(BaseRepository[AnalysisDataset]):
    """Repository for AnalysisDataset entity."""

    def __init__(self, db: Session):
        super().__init__(db, AnalysisDataset)

    def get_by_upload_id(self, upload_id: str) -> Optional[AnalysisDataset]:
        """Get analysis dataset by upload ID."""
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.upload_id == upload_id,
            AnalysisDataset.is_deleted == False
        ).first()

    def get_by_user(self, user_id: UUID) -> list:
        """Get analysis datasets by user."""
        return self.db.query(AnalysisDataset).filter(
            AnalysisDataset.user_id == user_id,
            AnalysisDataset.is_deleted == False
        ).all()