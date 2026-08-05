# app/application/mapping/command_mapper.py
"""
Command Mapper - DOCUMENT 07 APP-017 / REVISION 02

Maps incoming requests to Application Commands.

The mapper SHALL remain independent from REST.
Future communication channels (REST, CLI, WebSocket, Message Queue, Scheduler)
SHALL all reuse the same Command Mapper.
"""

from typing import Dict, Any, Optional
from uuid import UUID

from app.application.commands.base import (
    RunBusinessObjectiveCommand,
    RunSingleAnalysisCommand,
    UploadDatasetCommand,
    ValidateDatasetCommand,
    ApproveDatasetCommand,
    RetrieveArtifactCommand,
)
from app.api.v2.schemas.base_request import (
    BusinessObjectiveRequest,
    SingleAnalysisRequest,
    DatasetUploadRequest,
    DatasetValidateRequest,
    DatasetApproveRequest,
)


class CommandMapper:
    """
    Command Mapper - Maps requests to Application Commands.
    
    Independent from REST. Can be reused for CLI, WebSocket, etc.
    """
    
    @staticmethod
    def to_business_objective_command(
        request: BusinessObjectiveRequest,
        user_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> RunBusinessObjectiveCommand:
        """
        Map BusinessObjectiveRequest to RunBusinessObjectiveCommand.
        """
        return RunBusinessObjectiveCommand(
            user_id=user_id,
            company_id=request.company_id,
            objective_type=request.objective_type,
            dataset_id=request.dataset_id,
            params={
                **(request.params or {}),
                "config": request.config or {},
                "language": request.language,
                "client_version": request.client_version,
            },
            trace_id=trace_id or request.request_id,
            correlation_id=correlation_id,
        )
    
    @staticmethod
    def to_single_analysis_command(
        request: SingleAnalysisRequest,
        user_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> RunSingleAnalysisCommand:
        """
        Map SingleAnalysisRequest to RunSingleAnalysisCommand.
        """
        return RunSingleAnalysisCommand(
            user_id=user_id,
            company_id=request.company_id,
            analysis_type=request.analysis_type,
            dataset_id=request.dataset_id,
            material_codes=request.material_codes,
            params={
                **(request.params or {}),
                "config": request.config or {},
                "language": request.language,
                "client_version": request.client_version,
            },
            trace_id=trace_id or request.request_id,
            correlation_id=correlation_id,
        )
    
    @staticmethod
    def to_upload_dataset_command(
        request: DatasetUploadRequest,
        user_id: UUID,
        file_content: Any,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> UploadDatasetCommand:
        """
        Map DatasetUploadRequest to UploadDatasetCommand.
        """
        return UploadDatasetCommand(
            user_id=user_id,
            company_id=request.company_id,
            source_type=request.source_type,
            source_name=request.source_name,
            file_content=file_content,
            metadata={
                **(request.metadata or {}),
                "language": request.language,
                "client_version": request.client_version,
            },
            trace_id=trace_id or request.request_id,
            correlation_id=correlation_id,
        )
    
    @staticmethod
    def to_validate_dataset_command(
        request: DatasetValidateRequest,
        user_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> ValidateDatasetCommand:
        """
        Map DatasetValidateRequest to ValidateDatasetCommand.
        """
        return ValidateDatasetCommand(
            user_id=user_id,
            company_id=request.company_id,
            dataset_id=request.dataset_id,
            trace_id=trace_id or request.request_id,
            correlation_id=correlation_id,
        )
    
    @staticmethod
    def to_approve_dataset_command(
        request: DatasetApproveRequest,
        user_id: UUID,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> ApproveDatasetCommand:
        """
        Map DatasetApproveRequest to ApproveDatasetCommand.
        """
        return ApproveDatasetCommand(
            user_id=user_id,
            company_id=request.company_id,
            dataset_id=request.dataset_id,
            notes=request.notes,
            trace_id=trace_id or request.request_id,
            correlation_id=correlation_id,
        )