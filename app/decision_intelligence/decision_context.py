# app/decision_intelligence/decision_context.py
"""
Decision Context - DOCUMENT 06 - PART 01
Single runtime object passed through the Decision Intelligence pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID


@dataclass
class DecisionContext:
    """
    Decision Context - DOCUMENT 06
    
    Single runtime object passed through the Decision Intelligence pipeline.
    All extensions SHALL be added only through this context.
    """
    
    # ============================================
    # EXECUTION RESULTS
    # ============================================
    execution_id: UUID
    workflow_id: str
    business_objective: str
    execution_status: str
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # ============================================
    # RESULTS
    # ============================================
    forecast_results: Dict[str, Any] = field(default_factory=dict)
    safety_stock_results: Dict[str, Any] = field(default_factory=dict)
    simulation_results: Dict[str, Any] = field(default_factory=dict)
    backtest_results: Dict[str, Any] = field(default_factory=dict)
    supplier_results: Dict[str, Any] = field(default_factory=dict)
    
    # ============================================
    # LEARNING RESULTS
    # ============================================
    company_learning: Dict[str, Any] = field(default_factory=dict)
    pattern_intelligence: Dict[str, Any] = field(default_factory=dict)
    decision_learning: Dict[str, Any] = field(default_factory=dict)
    knowledge_maturity: Dict[str, Any] = field(default_factory=dict)
    
    # ============================================
    # DECISION SCORES
    # ============================================
    decision_scores: Dict[str, float] = field(default_factory=dict)
    
    # ============================================
    # COMPANY & DATASET
    # ============================================
    company_id: Optional[UUID] = None
    company_name: Optional[str] = None
    dataset_id: Optional[UUID] = None
    dataset_version: Optional[int] = None
    sector_id: Optional[UUID] = None
    
    # ============================================
    # USER
    # ============================================
    user_id: Optional[UUID] = None
    user_language: str = "Türkçe"
    user_role: str = "user"
    
    # ============================================
    # PROMPT
    # ============================================
    prompt_version: str = "1.0.0"
    prompt_template: Optional[str] = None
    
    # ============================================
    # NARRATIVE
    # ============================================
    narrative_id: Optional[str] = None
    narrative_version: int = 1
    generated_at: datetime = field(default_factory=datetime.now)
    
    # ============================================
    # METADATA
    # ============================================
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_regeneration: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            # Execution
            "execution_id": str(self.execution_id),
            "workflow_id": self.workflow_id,
            "business_objective": self.business_objective,
            "execution_status": self.execution_status,
            "execution_metrics": self.execution_metrics,
            
            # Results
            "forecast_results": self.forecast_results,
            "safety_stock_results": self.safety_stock_results,
            "simulation_results": self.simulation_results,
            "backtest_results": self.backtest_results,
            "supplier_results": self.supplier_results,
            
            # Learning
            "company_learning": self.company_learning,
            "pattern_intelligence": self.pattern_intelligence,
            "decision_learning": self.decision_learning,
            "knowledge_maturity": self.knowledge_maturity,
            
            # Scores
            "decision_scores": self.decision_scores,
            
            # Company & Dataset
            "company_id": str(self.company_id) if self.company_id else None,
            "company_name": self.company_name,
            "dataset_id": str(self.dataset_id) if self.dataset_id else None,
            "dataset_version": self.dataset_version,
            "sector_id": str(self.sector_id) if self.sector_id else None,
            
            # User
            "user_id": str(self.user_id) if self.user_id else None,
            "user_language": self.user_language,
            "user_role": self.user_role,
            
            # Prompt
            "prompt_version": self.prompt_version,
            "prompt_template": self.prompt_template,
            
            # Narrative
            "narrative_id": self.narrative_id,
            "narrative_version": self.narrative_version,
            "generated_at": self.generated_at.isoformat(),
            
            # Metadata
            "metadata": self.metadata,
            "is_regeneration": self.is_regeneration,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionContext':
        """Create context from dictionary."""
        return cls(
            execution_id=UUID(data["execution_id"]),
            workflow_id=data["workflow_id"],
            business_objective=data["business_objective"],
            execution_status=data.get("execution_status", "completed"),
            execution_metrics=data.get("execution_metrics", {}),
            forecast_results=data.get("forecast_results", {}),
            safety_stock_results=data.get("safety_stock_results", {}),
            simulation_results=data.get("simulation_results", {}),
            backtest_results=data.get("backtest_results", {}),
            supplier_results=data.get("supplier_results", {}),
            company_learning=data.get("company_learning", {}),
            pattern_intelligence=data.get("pattern_intelligence", {}),
            decision_learning=data.get("decision_learning", {}),
            knowledge_maturity=data.get("knowledge_maturity", {}),
            decision_scores=data.get("decision_scores", {}),
            company_id=UUID(data["company_id"]) if data.get("company_id") else None,
            company_name=data.get("company_name"),
            dataset_id=UUID(data["dataset_id"]) if data.get("dataset_id") else None,
            dataset_version=data.get("dataset_version"),
            sector_id=UUID(data["sector_id"]) if data.get("sector_id") else None,
            user_id=UUID(data["user_id"]) if data.get("user_id") else None,
            user_language=data.get("user_language", "Türkçe"),
            user_role=data.get("user_role", "user"),
            prompt_version=data.get("prompt_version", "1.0.0"),
            prompt_template=data.get("prompt_template"),
            narrative_id=data.get("narrative_id"),
            narrative_version=data.get("narrative_version", 1),
            generated_at=datetime.fromisoformat(data["generated_at"]) if "generated_at" in data else datetime.now(),
            metadata=data.get("metadata", {}),
            is_regeneration=data.get("is_regeneration", False),
        )
    
    def has_forecast(self) -> bool:
        """Check if forecast results exist."""
        return bool(self.forecast_results)
    
    def has_safety_stock(self) -> bool:
        """Check if safety stock results exist."""
        return bool(self.safety_stock_results)
    
    def has_simulation(self) -> bool:
        """Check if simulation results exist."""
        return bool(self.simulation_results)
    
    def has_backtest(self) -> bool:
        """Check if backtest results exist."""
        return bool(self.backtest_results)
    
    def has_supplier(self) -> bool:
        """Check if supplier results exist."""
        return bool(self.supplier_results)
    
    def has_learning(self) -> bool:
        """Check if learning results exist."""
        return bool(
            self.company_learning or
            self.pattern_intelligence or
            self.decision_learning or
            self.knowledge_maturity
        )
    
    def get_available_analyses(self) -> List[str]:
        """Get list of available analysis types."""
        analyses = []
        if self.has_forecast():
            analyses.append("forecast")
        if self.has_safety_stock():
            analyses.append("safety_stock")
        if self.has_simulation():
            analyses.append("simulation")
        if self.has_backtest():
            analyses.append("backtest")
        if self.has_supplier():
            analyses.append("supplier")
        return analyses
    
    def get_confidence_level(self) -> float:
        """Calculate overall confidence level."""
        confidence = 0.5  # Base confidence
        
        # Add learning confidence
        if self.knowledge_maturity:
            maturity = self.knowledge_maturity.get("overall_maturity", 0)
            confidence += maturity * 0.3
        
        # Add decision scores
        if self.decision_scores:
            avg_score = sum(self.decision_scores.values()) / len(self.decision_scores)
            confidence += avg_score * 0.2
        
        return round(min(1.0, confidence), 3)