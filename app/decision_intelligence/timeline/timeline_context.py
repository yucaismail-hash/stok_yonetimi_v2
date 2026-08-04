# app/decision_intelligence/timeline/timeline_context.py
"""
Timeline Context - DOCUMENT 06 - PART 03
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


@dataclass
class TimelineContext:
    """
    Timeline Context - DOCUMENT 06
    
    Single runtime object for Timeline Engine.
    """
    
    # Company
    company_id: UUID
    company_name: Optional[str] = None
    
    # Timeline Period
    timeline_period: str = "Last 6 Months"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Historical Narratives
    historical_narratives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Learning Evolution
    learning_evolution: Dict[str, Any] = field(default_factory=dict)
    
    # Knowledge Maturity
    knowledge_maturity: Dict[str, Any] = field(default_factory=dict)
    
    # User
    user_id: Optional[UUID] = None
    user_language: str = "Türkçe"
    
    # Prompt
    prompt_version: str = "1.0.0"
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_id": str(self.company_id),
            "company_name": self.company_name,
            "timeline_period": self.timeline_period,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "historical_narratives_count": len(self.historical_narratives),
            "learning_evolution": self.learning_evolution,
            "knowledge_maturity": self.knowledge_maturity,
            "user_id": str(self.user_id) if self.user_id else None,
            "user_language": self.user_language,
            "prompt_version": self.prompt_version,
            "generated_at": self.generated_at.isoformat(),
        }