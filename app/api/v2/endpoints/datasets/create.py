# app/api/v2/endpoints/datasets/create.py
"""
Dataset Create Endpoint - DOCUMENT 07 APP-015 / APP-016

POST /api/v2/datasets
"""

from fastapi import APIRouter, Depends, File, UploadFile
from typing import Optional
from uuid import UUID

from app.api.v2.schemas import DatasetUploadRequest, BaseResponse
from app.api.v2.dependencies.auth import get_user_id
from app.api.v2.middleware.trace import TraceContextHolder
from app.application.services.dataset.dataset_service import DatasetService
from app.application.mapping.command_mapper import CommandMapper

router = APIRouter(tags=["Datasets"])


@router.post(
    "",
    response_model=BaseResponse,
    status_code=201,
    summary="Upload Dataset",
    description="Upload a dataset for analysis.",
)
async def create_dataset(
    source_type: str,
    file: UploadFile = File(...),
    source_name: Optional[str] = None,
    user_id: UUID = Depends(get_user_id),
) -> BaseResponse:
    """
    Upload a dataset.
    """
    # Get trace context
    trace_context = TraceContextHolder.get_context()
    
    # Read file content
    file_content = await file.read()
    
    # Create request object
    request = DatasetUploadRequest(
        company_id=trace_context.company_id if trace_context else None,
        source_type=source_type,
        source_name=source_name or file.filename,
        metadata={
            "filename": file.filename,
            "content_type": file.content_type,
        },
    )
    
    # Map request to command
    command = CommandMapper.to_upload_dataset_command(
        request=request,
        user_id=user_id,
        file_content=file_content,
        trace_id=trace_context.trace_id if trace_context else None,
        correlation_id=trace_context.correlation_id if trace_context else None,
    )
    
    # Execute through service
    service = DatasetService()
    response = await service.upload_dataset(
        company_id=command.company_id,
        user_id=command.user_id,
        source_type=command.source_type,
        file_content=command.file_content,
        source_name=command.source_name,
        metadata=command.metadata,
        trace_id=command.trace_id,
        correlation_id=command.correlation_id,
    )
    
    return response