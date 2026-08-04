# app/decision_intelligence/advisor/executive_report_persistence.py
"""
Executive Report Persistence - DOCUMENT 06 - PART 04
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
import logging

from app.decision_intelligence.advisor.executive_memory import ExecutiveMemory
from app.decision_intelligence.timeline.ai_artifact_repository import AIArtifactRepository
from app.decision_intelligence.timeline.ai_artifact_serializer import AIArtifactSerializer

logger = logging.getLogger(__name__)


class ExecutiveReportPersistence:
    """
    Executive Report Persistence - EA-006
    
    Persists Executive Advisor Reports as AI Artifacts.
    """
    
    def __init__(self):
        self.memory = ExecutiveMemory()
        self.repository = AIArtifactRepository()
        self.serializer = AIArtifactSerializer()
    
    def save(self, report: Dict[str, Any], context) -> Dict[str, Any]:
        """Save report as AI Artifact."""
        report_id = str(uuid4())
        
        # Save to executive memory
        self.memory.add_report(str(context.company_id), {**report, "report_id": report_id})
        
        # Save as AI Artifact
        artifact = self.serializer.create_artifact(
            artifact_type="executive_advisor",
            company_id=str(context.company_id),
            execution_id="",
            structured_content=report,
            metadata={
                "timeline_period": context.executive_timeline.get("timeline_period", ""),
                "language": context.user_language,
                "prompt_version": context.prompt_version,
                "is_regeneration": context.is_regeneration,
            },
        )
        
        self.repository.save(artifact)
        
        logger.info(f"✅ Executive Advisor Report saved: {report_id}")
        
        return {
            "report_id": report_id,
            "artifact_id": artifact.get("artifact_id"),
            "saved_at": datetime.now().isoformat(),
        }
    
    def get_latest(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest report for a company."""
        return self.memory.get_latest(company_id)
    
    def get_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        return self.memory.get_report(report_id)