# app/decision_intelligence/advisor/executive_advisor_engine.py
"""
Executive Advisor Engine - DOCUMENT 06 - PART 04
Main orchestrator for Executive Advisor.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.decision_intelligence.advisor.executive_advisor_context import ExecutiveAdvisorContext
from app.decision_intelligence.advisor.strategic_recommendation_generator import StrategicRecommendationGenerator
from app.decision_intelligence.advisor.executive_report_persistence import ExecutiveReportPersistence
from app.decision_intelligence.advisor.executive_memory import ExecutiveMemory
from app.decision_intelligence.advisor.executive_explainability import ExecutiveExplainability
from app.decision_intelligence.advisor.structured_executive_report_builder import StructuredExecutiveReportBuilder

logger = logging.getLogger(__name__)


class ExecutiveAdvisorEngine:
    """
    Executive Advisor Engine - EA-001
    
    Main orchestrator for Executive Advisor.
    """
    
    def __init__(self):
        self.generator = StrategicRecommendationGenerator()
        self.persistence = ExecutiveReportPersistence()
        self.memory = ExecutiveMemory()
        self.explainability = ExecutiveExplainability()
        self.structured_builder = StructuredExecutiveReportBuilder()
    
    def generate_report(self, context: ExecutiveAdvisorContext) -> Dict[str, Any]:
        """
        Generate Executive Advisor Report.
        """
        logger.info(f"🎯 Executive Advisor started for: {context.company_name}")
        
        # 1. Check if report exists
        existing = self.memory.get_latest(str(context.company_id))
        if existing and not context.is_regeneration:
            logger.info(f"✅ Using existing report for: {context.company_name}")
            return {
                "status": "reused",
                "report": existing.get("report", {}),
                "metadata": {
                    "reused": True,
                    "generated_at": existing.get("created_at"),
                },
            }
        
        # 2. Generate strategic recommendations
        recommendations = self.generator.generate(context)
        
        # 3. Generate explainability
        recommendations["_explainability"] = self.explainability.explain(context, recommendations)
        
        # 4. Build structured report
        structured_report = self.structured_builder.build(recommendations, context)
        
        # 5. Persist
        saved = self.persistence.save(structured_report, context)
        
        logger.info(f"✅ Executive Advisor Report generated for: {context.company_name}")
        
        return {
            "status": "generated",
            "report": structured_report,
            "saved": saved,
            "metadata": {
                "reused": False,
                "generated_at": datetime.now().isoformat(),
                "is_regeneration": context.is_regeneration,
            },
        }
    
    def get_latest_report(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest report for a company."""
        return self.persistence.get_latest(company_id)
    
    def get_report_by_id(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        return self.persistence.get_by_id(report_id)
    
    def regenerate(self, context: ExecutiveAdvisorContext) -> Dict[str, Any]:
        """Force regenerate advisor report."""
        context.is_regeneration = True
        return self.generate_report(context)