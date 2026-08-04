# app/decision_intelligence/advisor/executive_advisor_context.py
"""
Executive Advisor Context - DOCUMENT 06 - PART 04
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class ExecutiveAdvisorContext:
    """
    Executive Advisor Context - DOCUMENT 06
    
    Single runtime object for Executive Advisor Engine.
    """
    
    # Company
    company_id: UUID
    company_name: Optional[str] = None
    
    # Executive Timeline
    executive_timeline: Dict[str, Any] = field(default_factory=dict)
    
    # Company Learning Summary
    company_learning_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Knowledge Maturity
    knowledge_maturity: Dict[str, Any] = field(default_factory=dict)
    
    # Historical Reports
    historical_reports: List[Dict[str, Any]] = field(default_factory=list)
    
    # User
    user_id: Optional[UUID] = None
    user_language: str = "Türkçe"
    user_role: str = "executive"
    
    # Prompt
    prompt_version: str = "1.0.0"
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    is_regeneration: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Report ID (generated when saving)
    report_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.
        """
        return {
            "company_id": str(self.company_id),
            "company_name": self.company_name,
            "executive_timeline": self.executive_timeline,
            "company_learning_summary": self.company_learning_summary,
            "knowledge_maturity": self.knowledge_maturity,
            "historical_reports_count": len(self.historical_reports),
            "historical_reports": self.historical_reports,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_language": self.user_language,
            "user_role": self.user_role,
            "prompt_version": self.prompt_version,
            "generated_at": self.generated_at.isoformat(),
            "is_regeneration": self.is_regeneration,
            "metadata": self.metadata,
            "report_id": self.report_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutiveAdvisorContext':
        """
        Create context from dictionary.
        """
        return cls(
            company_id=UUID(data["company_id"]),
            company_name=data.get("company_name"),
            executive_timeline=data.get("executive_timeline", {}),
            company_learning_summary=data.get("company_learning_summary", {}),
            knowledge_maturity=data.get("knowledge_maturity", {}),
            historical_reports=data.get("historical_reports", []),
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            user_language=data.get("user_language", "Türkçe"),
            user_role=data.get("user_role", "executive"),
            prompt_version=data.get("prompt_version", "1.0.0"),
            generated_at=datetime.fromisoformat(data["generated_at"]) if "generated_at" in data else datetime.now(),
            is_regeneration=data.get("is_regeneration", False),
            metadata=data.get("metadata", {}),
            report_id=data.get("report_id"),
        )
    
    def to_prompt_context(self) -> Dict[str, Any]:
        """
        Extract only the information needed for prompt generation.
        """
        return {
            "company_name": self.company_name,
            "company_id": str(self.company_id),
            "timeline_period": self.executive_timeline.get("timeline_period", ""),
            "executive_overview": self.executive_timeline.get("executive_overview", ""),
            "major_improvements": self.executive_timeline.get("major_improvements", []),
            "major_risks": self.executive_timeline.get("major_risks", []),
            "trend_summary": self.executive_timeline.get("trend_summary", []),
            "recommended_focus": self.executive_timeline.get("recommended_focus", []),
            "learning_maturity": self.knowledge_maturity.get("maturity_level", "unknown"),
            "learning_score": self.knowledge_maturity.get("overall_maturity", 0),
            "historical_reports_count": len(self.historical_reports),
            "user_language": self.user_language,
        }
    
    def has_timeline(self) -> bool:
        """Check if executive timeline exists."""
        return bool(self.executive_timeline)
    
    def has_learning_summary(self) -> bool:
        """Check if learning summary exists."""
        return bool(self.company_learning_summary)
    
    def has_knowledge_maturity(self) -> bool:
        """Check if knowledge maturity exists."""
        return bool(self.knowledge_maturity)
    
    def get_timeline_period(self) -> str:
        """Get timeline period."""
        return self.executive_timeline.get("timeline_period", "Bilinmiyor")
    
    def get_maturity_level(self) -> str:
        """Get maturity level."""
        return self.knowledge_maturity.get("maturity_level", "unknown")
    
    def generate_report_id(self) -> str:
        """Generate a new report ID."""
        self.report_id = str(uuid4())
        return self.report_id