# app/decision_intelligence/timeline/timeline_engine.py
"""
Executive Timeline Engine - DOCUMENT 06 - PART 03
Main orchestrator for Executive Timeline.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.decision_intelligence.timeline.timeline_context import TimelineContext
from app.decision_intelligence.timeline.timeline_generator import TimelineGenerator
from app.decision_intelligence.timeline.timeline_persistence import TimelinePersistence
from app.decision_intelligence.timeline.timeline_reuse_manager import TimelineReuseManager
from app.decision_intelligence.timeline.ai_artifact_repository import AIArtifactRepository
from app.decision_intelligence.timeline.structured_timeline_builder import StructuredTimelineBuilder

logger = logging.getLogger(__name__)


class ExecutiveTimelineEngine:
    """
    Executive Timeline Engine - TL-001
    
    Main orchestrator for Executive Timeline generation.
    """
    
    def __init__(self):
        self.generator = TimelineGenerator()
        self.persistence = TimelinePersistence()
        self.reuse_manager = TimelineReuseManager()
        self.repository = AIArtifactRepository()
        self.structured_builder = StructuredTimelineBuilder()
    
    def generate_timeline(self, context: TimelineContext) -> Dict[str, Any]:
        """
        Generate or retrieve Executive Timeline.
        """
        logger.info(f"📅 Executive Timeline started for: {context.company_name}")
        
        # 1. Check if timeline exists
        existing = self.reuse_manager.get_reusable_timeline(context)
        if existing:
            logger.info(f"✅ Using existing timeline for: {context.company_name}")
            return {
                "status": "reused",
                "timeline": existing.get("structured_content", {}),
                "artifact_id": existing.get("artifact_id"),
                "metadata": {
                    "reused": True,
                    "generated_at": existing.get("created_at"),
                },
            }
        
        # 2. Generate new timeline
        timeline = self.generator.generate(context)
        
        # 3. Persist as AI Artifact
        saved = self.persistence.save(timeline, context)
        
        # 4. Build structured response
        structured = self.structured_builder.build(timeline, context)
        
        logger.info(f"✅ Executive Timeline generated for: {context.company_name}")
        
        return {
            "status": "generated",
            "timeline": structured,
            "artifact_id": saved.get("artifact_id"),
            "metadata": {
                "reused": False,
                "generated_at": datetime.now().isoformat(),
                "narratives_analyzed": len(context.historical_narratives),
            },
        }
    
    def get_timeline(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest timeline for a company."""
        return self.repository.get_latest_timeline(company_id)
    
    def get_timeline_by_id(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Get timeline by artifact ID."""
        return self.repository.get(artifact_id)
    
    def regenerate(self, context: TimelineContext) -> Dict[str, Any]:
        """Force regenerate timeline."""
        context.metadata["force_regeneration"] = True
        return self.generate_timeline(context)
