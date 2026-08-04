# app/repositories/base.py
"""
Base Repository - Tüm repository'ler için temel sınıf.
"""

from typing import Optional, List, Dict, Any, Type, Generic, TypeVar
from uuid import UUID
from sqlalchemy.orm import Session, Query
from sqlalchemy import func

from app.models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with CRUD operations."""

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get_by_id(self, entity_id: UUID) -> Optional[T]:
        """Get entity by UUID."""
        return self.db.query(self.model).filter(
            self.model.id == entity_id,
            self.model.is_deleted == False
        ).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        return self.db.query(self.model).filter(
            self.model.is_deleted == False
        ).offset(skip).limit(limit).all()

    def get_by_company(self, company_id: UUID, skip: int = 0, limit: int = 100) -> List[T]:
        """Get entities by company ID."""
        return self.db.query(self.model).filter(
            self.model.company_id == company_id,
            self.model.is_deleted == False
        ).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> T:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.db.add(entity)
        self.db.flush()
        return entity

    def create_bulk(self, items: List[Dict[str, Any]]) -> List[T]:
        """Create multiple entities."""
        entities = [self.model(**item) for item in items]
        self.db.add_all(entities)
        self.db.flush()
        return entities

    def update(self, entity_id: UUID, **kwargs) -> Optional[T]:
        """Update an entity."""
        entity = self.get_by_id(entity_id)
        if not entity:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        self.db.flush()
        return entity

    def soft_delete(self, entity_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete an entity."""
        entity = self.get_by_id(entity_id)
        if not entity:
            return False
        entity.soft_delete(deleted_by)
        self.db.flush()
        return True

    def restore(self, entity_id: UUID) -> bool:
        """Restore a soft deleted entity."""
        entity = self.db.query(self.model).filter(
            self.model.id == entity_id,
            self.model.is_deleted == True
        ).first()
        if not entity:
            return False
        entity.restore()
        self.db.flush()
        return True

    def count(self, company_id: Optional[UUID] = None) -> int:
        """Count entities."""
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        if company_id:
            query = query.filter(self.model.company_id == company_id)
        return query.count()

    def exists(self, entity_id: UUID) -> bool:
        """Check if entity exists."""
        return self.db.query(self.model).filter(
            self.model.id == entity_id,
            self.model.is_deleted == False
        ).first() is not None

    def commit(self):
        """Commit the current transaction."""
        self.db.commit()

    def rollback(self):
        """Rollback the current transaction."""
        self.db.rollback()