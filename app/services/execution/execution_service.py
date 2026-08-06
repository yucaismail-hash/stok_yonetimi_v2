"""
Official public facade for execution use cases.

The facade delegates application-layer execution operations without owning
workflow, runtime, persistence, learning, decision, or artifact behavior.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from app.application.response.schemas import APIResponse


class ExecutionService:
    """Public facade delegating execution use cases to the Application Layer."""

    def __init__(self, _delegate: Any = None):
        if _delegate is None:
            from app.application.services.execution.execution_service import (
                ExecutionService as ApplicationExecutionService,
            )

            _delegate = ApplicationExecutionService()

        self._delegate = _delegate

    async def run_analysis(
        self,
        company_id: UUID,
        user_id: UUID,
        dataset_id: UUID,
        analysis_type: str,
        material_codes: Optional[list[str]] = None,
        params: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> APIResponse:
        return await self._delegate.run_analysis(
            company_id=company_id,
            user_id=user_id,
            dataset_id=dataset_id,
            analysis_type=analysis_type,
            material_codes=material_codes,
            params=params,
            trace_id=trace_id,
            correlation_id=correlation_id,
        )

    async def get_execution_status(
        self,
        execution_id: UUID,
        trace_id: Optional[str] = None,
    ) -> APIResponse:
        return await self._delegate.get_execution_status(
            execution_id=execution_id,
            trace_id=trace_id,
        )

    async def get_execution_result(
        self,
        execution_id: UUID,
        trace_id: Optional[str] = None,
    ) -> APIResponse:
        return await self._delegate.get_execution_result(
            execution_id=execution_id,
            trace_id=trace_id,
        )
