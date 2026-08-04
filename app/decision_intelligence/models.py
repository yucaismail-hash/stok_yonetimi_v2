# app/decision_intelligence/models.py
"""
Decision Intelligence Models - DOCUMENT 06 - PART 01
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


@dataclass
class DecisionNarrative:
    """Complete decision narrative."""
    narrative_id: str = field(default_factory=lambda: str(uuid4()))
    execution_id: str = ""
    workflow_id: str = ""
    business_objective: str = ""
    
    summary: str = ""
    findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timeline: str = ""
    confidence: float = 0.5
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: int = 1
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_regeneration: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "narrative_id": self.narrative_id,
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "business_objective": self.business_objective,
            "summary": self.summary,
            "findings": self.findings,
            "risks": self.risks,
            "opportunities": self.opportunities,
            "recommendations": self.recommendations,
            "timeline": self.timeline,
            "confidence": self.confidence,
            "metadata": self.metadata,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_regeneration": self.is_regeneration,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionNarrative':
        """Create from dictionary."""
        return cls(
            narrative_id=data.get("narrative_id", str(uuid4())),
            execution_id=data.get("execution_id", ""),
            workflow_id=data.get("workflow_id", ""),
            business_objective=data.get("business_objective", ""),
            summary=data.get("summary", ""),
            findings=data.get("findings", []),
            risks=data.get("risks", []),
            opportunities=data.get("opportunities", []),
            recommendations=data.get("recommendations", []),
            timeline=data.get("timeline", ""),
            confidence=data.get("confidence", 0.5),
            metadata=data.get("metadata", {}),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            is_regeneration=data.get("is_regeneration", False),
        )