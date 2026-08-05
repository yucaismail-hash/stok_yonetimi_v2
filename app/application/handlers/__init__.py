# app/application/handlers/__init__.py
"""
Command Handlers - DOCUMENT 07 REVISION 03

Command Handlers SHALL become responsible for:
- Command execution
- Workflow preparation
- Transaction coordination
- Service invocation
"""

from app.application.handlers.base import BaseHandler
from app.application.handlers.run_business_objective_handler import RunBusinessObjectiveHandler
from app.application.handlers.run_single_analysis_handler import RunSingleAnalysisHandler
from app.application.handlers.upload_dataset_handler import UploadDatasetHandler
from app.application.handlers.validate_dataset_handler import ValidateDatasetHandler
from app.application.handlers.approve_dataset_handler import ApproveDatasetHandler
from app.application.handlers.retrieve_artifact_handler import RetrieveArtifactHandler

__all__ = [
    "BaseHandler",
    "RunBusinessObjectiveHandler",
    "RunSingleAnalysisHandler",
    "UploadDatasetHandler",
    "ValidateDatasetHandler",
    "ApproveDatasetHandler",
    "RetrieveArtifactHandler",
]