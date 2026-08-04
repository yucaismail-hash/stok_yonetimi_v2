# app/repositories/company_repository.py
"""
Company Repository
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.company import Company
from app.repositories.base import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company entity."""

    def __init__(self, db: Session):
        super().__init__(db, Company)

    def get_by_tax_id(self, tax_id: str) -> Optional[Company]:
        """Get company by tax ID."""
        return self.db.query(Company).filter(
            Company.tax_id == tax_id,
            Company.is_deleted == False
        ).first()

    def get_active_companies(self, skip: int = 0, limit: int = 100) -> List[Company]:
        """Get all active companies."""
        return self.db.query(Company).filter(
            Company.is_active == True,
            Company.is_deleted == False
        ).offset(skip).limit(limit).all()

    def get_users(self, company_id: UUID) -> List:
        """Get all users of a company."""
        company = self.get_by_id(company_id)
        if company:
            return company.users
        return []

    def get_datasets(self, company_id: UUID) -> List:
        """Get all datasets of a company."""
        company = self.get_by_id(company_id)
        if company:
            return company.datasets
        return []