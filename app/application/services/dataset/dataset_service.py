# app/application/services/dataset/dataset_service.py
"""
Dataset Service - DOCUMENT 07 REVISION 02
Domain-based application service for dataset operations.

Application Services SHALL:
- Validate business requests
- Coordinate command handlers
- Coordinate workflows
- Coordinate transactions
- Generate responses

Application Services SHALL NEVER:
- Execute analytical logic
- Create AI Artifacts
- Perform learning
- Perform persistence directly
"""

from typing import Optional, Dict, Any, Union
from uuid import UUID
import logging

from app.application.commands.base import UploadDatasetCommand, ValidateDatasetCommand, ApproveDatasetCommand
from app.application.handlers.upload_dataset_handler import UploadDatasetHandler
from app.application.handlers.validate_dataset_handler import ValidateDatasetHandler
from app.application.handlers.approve_dataset_handler import ApproveDatasetHandler
from app.application.response.schemas import APIResponse

logger = logging.getLogger(__name__)


class DatasetService:
    """
    Dataset Service - Domain-based application service.
    
    Responsible for dataset orchestration.
    """
    
    def __init__(self):
        self.upload_handler = UploadDatasetHandler()
        self.validate_handler = ValidateDatasetHandler()
        self.approve_handler = ApproveDatasetHandler()
    
    async def upload_dataset(
        self,
        company_id: UUID,
        user_id: UUID,
        source_type: str,
        file_content: Any,
        source_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Upload a dataset.
        
        Args:
            company_id: Company ID
            user_id: User ID
            source_type: excel, csv, api
            file_content: File content
            source_name: Source name
            metadata: Additional metadata
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with dataset_id
        """
        logger.info(
            f"📤 DatasetService.upload_dataset: {source_type}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "source_type": source_type,
                "source_name": source_name,
            }
        )
        
        # Validate business request
        self._validate_source_type(source_type)
        
        # Create command
        command = UploadDatasetCommand(
            user_id=user_id,
            company_id=company_id,
            source_type=source_type,
            source_name=source_name,
            file_content=file_content,
            metadata=metadata,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.upload_handler.handle(command)
    
    async def validate_dataset(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Validate a dataset.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with validation result
        """
        logger.info(
            f"🔍 DatasetService.validate_dataset: {dataset_id}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
            }
        )
        
        # Create command
        command = ValidateDatasetCommand(
            user_id=user_id,
            company_id=company_id,
            dataset_id=dataset_id,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.validate_handler.handle(command)
    
    async def approve_dataset(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        notes: Optional[str] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        """
        Approve a dataset.
        
        Args:
            company_id: Company ID
            user_id: User ID
            dataset_id: Dataset ID
            notes: Approval notes
            trace_id: Trace ID for tracking
            correlation_id: Correlation ID for business flow
        
        Returns:
            APIResponse with approval result
        """
        logger.info(
            f"✅ DatasetService.approve_dataset: {dataset_id}",
            extra={
                "company_id": str(company_id),
                "user_id": str(user_id),
                "dataset_id": str(dataset_id),
            }
        )
        
        # Create command
        command = ApproveDatasetCommand(
            user_id=user_id,
            company_id=company_id,
            dataset_id=dataset_id,
            notes=notes,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )
        
        # Execute through handler
        return await self.approve_handler.handle(command)
    
    def _validate_source_type(self, source_type: str) -> None:
        """Validate source type."""
        valid_types = ["excel", "csv", "api"]
        if source_type not in valid_types:
            raise ValueError(f"Invalid source type: {source_type}. Must be one of: {valid_types}")