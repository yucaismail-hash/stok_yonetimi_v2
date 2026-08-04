# app/learning/company_learning.py
"""
Company Learning Engine - DOCUMENT 05 - PART 02A
Learns company-specific operational behaviour.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import statistics

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import CompanyLearningMemory


logger = logging.getLogger(__name__)


class CompanyMemory:
    """
    Company Memory - DOCUMENT 05 - PART 02A
    
    Contains two independent layers:
    - Stable Memory: Long-term company characteristics
    - Adaptive Memory: Recently observed behaviour
    """
    
    def __init__(self):
        # Stable Memory - Long-term
        self.stable: Dict[str, Any] = {}
        
        # Adaptive Memory - Recent
        self.adaptive: Dict[str, Any] = {}
        
        # Confidence
        self.confidence: float = 0.0
        
        # Profile
        self.profile: Dict[str, Any] = {}
        
        # Version tracking
        self.knowledge_version: int = 0
        self.last_updated: Optional[datetime] = None
        self.created_at: Optional[datetime] = None


class CompanyLearningEngine:
    """
    Company Learning Engine - DOCUMENT 05 - PART 02A
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        
        # Memory cache
        self._memories: Dict[UUID, CompanyMemory] = {}
        
        # Configuration
        self.adaptive_window_days = 30
        self.stable_decay_rate = 0.01
        self.confidence_threshold = 0.7
        self.min_observations_for_stable = 5
    
    def learn(self, context: LearningContext) -> Dict[str, Any]:
        """
        Main learning method - DOCUMENT 05 - PART 02A
        """
        # 1. Get or create company memory (Cold Start)
        memory = self._get_or_create_memory(context.company_id)
        
        # 2. Validate learning sources (only successful executions)
        if not self._is_valid_learning_source(context):
            return {
                "success": False,
                "reason": "Invalid learning source - execution not successful",
                "memory": {
                    "stable": memory.stable,
                    "adaptive": memory.adaptive,
                    "confidence": memory.confidence,
                }
            }
        
        # 3. Extract learnable information
        learnable = self._extract_learnable(context)
        
        # 4. Update Adaptive Memory
        adaptive_updates = self._update_adaptive_memory(memory, learnable)
        
        # 5. Update Stable Memory (if enough confidence)
        stable_updates = self._update_stable_memory(memory, learnable)
        
        # 6. Update Company Profile
        profile_updates = self._update_profile(memory)
        
        # 7. Calculate Company Confidence
        confidence = self._calculate_confidence(memory)
        memory.confidence = confidence
        
        # 8. Increment knowledge version
        memory.knowledge_version += 1
        
        # 9. Persist learnings
        saved_rules = self._persist_learnings(
            context,
            memory,
            adaptive_updates,
            stable_updates,
        )
        
        # 10. Explain the learning
        explanation = self._explain_learning(
            context,
            memory,
            adaptive_updates,
            stable_updates,
            confidence,
        )
        
        return {
            "success": True,
            "memory": {
                "stable": memory.stable,
                "adaptive": memory.adaptive,
                "confidence": memory.confidence,
                "profile": memory.profile,
                "knowledge_version": memory.knowledge_version,
            },
            "adaptive_updates": adaptive_updates,
            "stable_updates": stable_updates,
            "confidence_score": confidence,
            "saved_rules": saved_rules,
            "explanation": explanation,
        }
    
    def _get_or_create_memory(self, company_id: UUID) -> CompanyMemory:
        """Get existing memory or create new (Cold Start)."""
        if company_id not in self._memories:
            memory = CompanyMemory()
            memory.created_at = datetime.now()
            
            # Cold Start - DOCUMENT 05 - PART 02A Section 4
            memory.stable = {
                "planning_consistency": 0.5,
                "service_level_preference": 0.95,
                "demand_volatility_factor": 1.0,
                "lead_time_variability_factor": 1.0,
                "forecast_stability": 0.7,
                "inventory_characteristics": {
                    "avg_holding_rate": 0.2,
                    "avg_shortage_cost": 500.0,
                },
                "execution_characteristics": {
                    "avg_success_rate": 0.9,
                    "avg_retry_rate": 0.05,
                },
            }
            memory.adaptive = {}
            memory.confidence = 0.1
            memory.knowledge_version = 0
            memory.last_updated = datetime.now()
            
            self._memories[company_id] = memory
            
            logger.info(f"🆕 Cold start memory created for company: {company_id}")
        
        return self._memories[company_id]
    
    def _is_valid_learning_source(self, context: LearningContext) -> bool:
        """Validate learning source - only successful executions."""
        # Check execution status
        metrics = context.execution_metrics
        if metrics.get("status") not in ["completed", "success"]:
            return False
        
        # Check simulation results
        sim = context.simulation_results
        if sim and sim.get("status") == "failed":
            return False
        
        # Check backtest results
        backtest = context.backtest_results
        if backtest and backtest.get("status") == "failed":
            return False
        
        return True
    
    def _extract_learnable(self, context: LearningContext) -> Dict[str, Any]:
        """Extract learnable information from context."""
        learnable = {
            "timestamp": context.triggered_at,
            "execution_id": context.execution_id,
            "business_objective": context.business_objective,
            "execution_metrics": context.execution_metrics,
            "simulation_results": context.simulation_results,
            "backtest_results": context.backtest_results,
            "user_feedback": context.user_feedback,
            "user_rating": context.user_rating,
        }
        
        metrics = context.execution_metrics
        learnable["execution_success"] = metrics.get("status") == "completed"
        learnable["execution_duration_ms"] = metrics.get("total_duration_ms")
        
        sim = context.simulation_results
        if sim:
            learnable["observed_service_level"] = sim.get("service_level")
            learnable["observed_cvar"] = sim.get("cvar_95")
            learnable["observed_risk"] = sim.get("tail_risk")
        
        feedback = context.user_feedback
        if feedback:
            learnable["feedback_rating"] = feedback.get("rating")
            learnable["feedback_type"] = feedback.get("type")
        
        return learnable
    
    def _update_adaptive_memory(self, memory: CompanyMemory, learnable: Dict[str, Any]) -> Dict[str, Any]:
        """Update Adaptive Memory - DOCUMENT 05 - PART 02A Section 3."""
        updates = {}
        
        if not learnable.get("execution_success", False):
            return updates
        
        recent_key = f"recent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        memory.adaptive[recent_key] = {
            "timestamp": learnable["timestamp"].isoformat(),
            "duration_ms": learnable.get("execution_duration_ms"),
            "service_level": learnable.get("observed_service_level"),
            "cvar": learnable.get("observed_cvar"),
            "risk": learnable.get("observed_risk"),
            "feedback_rating": learnable.get("feedback_rating"),
            "business_objective": learnable.get("business_objective"),
        }
        
        updates["new_observation"] = recent_key
        updates["total_observations"] = len(memory.adaptive)
        
        # Apply knowledge decay
        self._apply_decay(memory)
        
        return updates
    
    def _update_stable_memory(self, memory: CompanyMemory, learnable: Dict[str, Any]) -> Dict[str, Any]:
        """Update Stable Memory - DOCUMENT 05 - PART 02A Section 3."""
        updates = {}
        
        if memory.confidence < self.confidence_threshold:
            return updates
        
        if len(memory.adaptive) < self.min_observations_for_stable:
            return updates
        
        service_levels = [
            v.get("service_level")
            for v in memory.adaptive.values()
            if v.get("service_level") is not None
        ]
        
        if service_levels:
            avg_service = statistics.mean(service_levels)
            old = memory.stable.get("service_level_preference", 0.95)
            new = (old * 0.7) + (avg_service * 0.3)
            memory.stable["service_level_preference"] = round(new, 3)
            updates["service_level_preference"] = {"old": round(old, 3), "new": round(new, 3)}
        
        if len(service_levels) >= 3:
            consistency = 1.0 - (statistics.stdev(service_levels) / max(service_levels))
            consistency = max(0, min(1, consistency))
            old = memory.stable.get("planning_consistency", 0.5)
            new = (old * 0.8) + (consistency * 0.2)
            memory.stable["planning_consistency"] = round(new, 3)
            updates["planning_consistency"] = {"old": round(old, 3), "new": round(new, 3)}
        
        return updates
    
    def _apply_decay(self, memory: CompanyMemory):
        """Apply knowledge decay - DOCUMENT 05 - PART 02A Section 8."""
        now = datetime.now()
        to_remove = []
        
        for key, value in memory.adaptive.items():
            timestamp = value.get("timestamp")
            if timestamp:
                try:
                    ts = datetime.fromisoformat(timestamp)
                    age_days = (now - ts).days
                    if age_days > self.adaptive_window_days:
                        to_remove.append(key)
                except:
                    continue
        
        for key in to_remove:
            del memory.adaptive[key]
        
        if to_remove:
            logger.debug(f"Decayed {len(to_remove)} adaptive memory entries")
    
    def _update_profile(self, memory: CompanyMemory) -> Dict[str, Any]:
        """Update Company Profile - DOCUMENT 05 - PART 02A Section 6."""
        profile = {
            "demand_volatility": self._calculate_demand_volatility(memory),
            "lead_time_variability": self._calculate_lead_time_variability(memory),
            "planning_consistency": memory.stable.get("planning_consistency", 0.5),
            "forecast_stability": memory.stable.get("forecast_stability", 0.7),
            "inventory_characteristics": memory.stable.get("inventory_characteristics", {}),
            "execution_characteristics": memory.stable.get("execution_characteristics", {}),
        }
        
        memory.profile = profile
        return profile
    
    def _calculate_demand_volatility(self, memory: CompanyMemory) -> float:
        return memory.stable.get("demand_volatility_factor", 1.0)
    
    def _calculate_lead_time_variability(self, memory: CompanyMemory) -> float:
        return memory.stable.get("lead_time_variability_factor", 1.0)
    
    def _calculate_confidence(self, memory: CompanyMemory) -> float:
        """Calculate Company Confidence Score - DOCUMENT 05 - PART 02A Section 9."""
        confidence = 0.0
        
        adaptive_count = len(memory.adaptive)
        if adaptive_count >= 10:
            confidence += 0.3
        elif adaptive_count >= 5:
            confidence += 0.15
        else:
            confidence += 0.05
        
        service_level = memory.stable.get("service_level_preference", 0.95)
        if 0.8 <= service_level <= 0.99:
            confidence += 0.2
        else:
            confidence += 0.05
        
        confidence += min(0.2, memory.knowledge_version * 0.02)
        
        consistency = memory.stable.get("planning_consistency", 0.5)
        confidence += consistency * 0.15
        
        confidence += 0.1
        
        return round(min(1.0, confidence), 3)
    
    def _persist_learnings(
        self,
        context: LearningContext,
        memory: CompanyMemory,
        adaptive_updates: Dict[str, Any],
        stable_updates: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Persist learnings to database."""
        saved_rules = []
        
        for key, value in stable_updates.items():
            rule = CompanyLearningMemory(
                company_id=context.company_id,
                user_id=context.user_id,
                rule_id=f"company_{key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                rule_name=f"Company {key.replace('_', ' ').title()}",
                rule_type="stable_update",
                description=f"Stable memory update: {key}",
                pattern_data={
                    "key": key,
                    "old_value": value.get("old"),
                    "new_value": value.get("new"),
                    "execution_id": str(context.execution_id),
                },
                confidence_score=memory.confidence,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=memory.confidence > 0.8,
            )
            
            self.db.add(rule)
            saved_rules.append({
                "rule_id": rule.rule_id,
                "type": key,
                "old_value": value.get("old"),
                "new_value": value.get("new"),
            })
        
        if saved_rules:
            self.db.flush()
            logger.info(f"📝 Persisted {len(saved_rules)} company learning rules")
        
        return saved_rules
    
    def _explain_learning(
        self,
        context: LearningContext,
        memory: CompanyMemory,
        adaptive_updates: Dict[str, Any],
        stable_updates: Dict[str, Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Explain the learning - DOCUMENT 05 - PART 02A Section 11."""
        return {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "confidence_before": memory.confidence,
            "confidence_after": confidence,
            "confidence_change": round(confidence - memory.confidence, 3),
            "adaptive_updates": len(adaptive_updates),
            "stable_updates": len(stable_updates),
            "memory_size": len(memory.adaptive),
            "knowledge_version": memory.knowledge_version,
            "timestamp": datetime.now().isoformat(),
        }