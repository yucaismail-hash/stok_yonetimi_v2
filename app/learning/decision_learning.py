# app/learning/decision_learning.py
"""
Decision Learning Engine - DOCUMENT 05 - PART 04
Learns decision quality from historical decision outcomes.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import statistics

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import CompanyAIMemory, CompanyLearningMemory


logger = logging.getLogger(__name__)


class DecisionMemory:
    """
    Decision Memory - DOCUMENT 05 - PART 04 Section 5
    
    Contains two independent layers:
    - Stable Decision: Long-term decision behaviour
    - Adaptive Decision: Recently observed behaviour
    """
    
    def __init__(self):
        # Stable Decision - Long-term
        self.stable: Dict[str, Any] = {}
        
        # Adaptive Decision - Recent
        self.adaptive: Dict[str, Any] = {}
        
        # Confidence
        self.confidence: float = 0.0
        
        # Decision Scores
        self.scores: Dict[str, float] = {}
        
        # Version tracking
        self.decision_version: int = 0
        self.last_updated: Optional[datetime] = None
        self.created_at: Optional[datetime] = None


class DecisionScoreManager:
    """
    Decision Score Manager - DOCUMENT 05 - PART 04 Section 8
    Maintains decision scores for different decision types.
    """
    
    def __init__(self):
        self._scores: Dict[str, List[float]] = {}
    
    def add_observation(self, decision_type: str, score: float):
        """Add a decision score observation."""
        if decision_type not in self._scores:
            self._scores[decision_type] = []
        self._scores[decision_type].append(score)
        
        # Limit history
        if len(self._scores[decision_type]) > 100:
            self._scores[decision_type] = self._scores[decision_type][-100:]
    
    def get_score(self, decision_type: str) -> float:
        """Get current decision score."""
        if decision_type not in self._scores or not self._scores[decision_type]:
            return 0.5  # Default
        
        # Weighted average (recent observations have higher weight)
        scores = self._scores[decision_type]
        n = len(scores)
        
        # Exponential weighting
        weighted_sum = 0
        total_weight = 0
        
        for i, score in enumerate(scores):
            weight = 1.5 ** (i / n)  # Increasing weight for recent
            weighted_sum += score * weight
            total_weight += weight
        
        return round(weighted_sum / total_weight if total_weight > 0 else 0.5, 3)
    
    def get_all_scores(self) -> Dict[str, float]:
        """Get all decision scores."""
        return {dt: self.get_score(dt) for dt in self._scores}


class DecisionLearningEngine:
    """
    Decision Learning Engine - DOCUMENT 05 - PART 04
    
    Learns decision quality from historical decision outcomes.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.score_manager = DecisionScoreManager()
        
        # Memory cache
        self._memories: Dict[UUID, DecisionMemory] = {}
        
        # Configuration
        self.adaptive_window_days = 30
        self.min_observations_for_stable = 5
        self.confidence_threshold = 0.6
    
    def learn(self, context: LearningContext) -> Dict[str, Any]:
        """
        Main learning method - DOCUMENT 05 - PART 04
        
        Learns decision quality from execution results.
        """
        # 1. Get or create decision memory
        memory = self._get_or_create_memory(context.company_id)
        
        # 2. Extract decision outcomes
        decisions = self._extract_decisions(context)
        
        # 3. Evaluate decision quality
        evaluated = self._evaluate_decisions(decisions, context)
        
        # 4. Update Adaptive Decision
        adaptive_updates = self._update_adaptive_decision(memory, evaluated)
        
        # 5. Update Stable Decision (if enough confidence)
        stable_updates = self._update_stable_decision(memory, evaluated)
        
        # 6. Update Decision Scores
        score_updates = self._update_decision_scores(memory, evaluated)
        
        # 7. Calculate Decision Confidence
        confidence = self._calculate_decision_confidence(memory, evaluated)
        memory.confidence = confidence
        
        # 8. Increment decision version
        memory.decision_version += 1
        
        # 9. Persist to database
        saved_decisions = self._persist_decisions(
            context,
            memory,
            evaluated,
            confidence,
        )
        
        # 10. Explain the learning
        explanation = self._explain_learning(
            context,
            memory,
            adaptive_updates,
            stable_updates,
            score_updates,
            confidence,
        )
        
        return {
            "memory": {
                "stable": memory.stable,
                "adaptive": memory.adaptive,
                "confidence": memory.confidence,
                "scores": memory.scores,
                "decision_version": memory.decision_version,
            },
            "evaluated_decisions": evaluated,
            "adaptive_updates": adaptive_updates,
            "stable_updates": stable_updates,
            "score_updates": score_updates,
            "confidence_score": confidence,
            "saved_decisions": saved_decisions,
            "explanation": explanation,
        }
    
    def _get_or_create_memory(self, company_id: UUID) -> DecisionMemory:
        """Get existing decision memory or create new."""
        if company_id not in self._memories:
            memory = DecisionMemory()
            memory.created_at = datetime.now()
            
            # Cold Start
            memory.stable = {
                "forecast_decision_consistency": 0.5,
                "safety_stock_decision_consistency": 0.5,
                "supplier_decision_consistency": 0.5,
                "simulation_performance": 0.5,
                "backtest_performance": 0.5,
            }
            memory.adaptive = {}
            memory.confidence = 0.1
            memory.decision_version = 0
            memory.last_updated = datetime.now()
            memory.scores = {
                "forecast": 0.5,
                "safety_stock": 0.5,
                "supplier": 0.5,
            }
            
            self._memories[company_id] = memory
            
            logger.info(f"🆕 Decision memory created for company: {company_id}")
        
        return self._memories[company_id]
    
    def _extract_decisions(self, context: LearningContext) -> Dict[str, Any]:
        """Extract decisions from context."""
        decisions = {}
        
        # Extract from business objective
        decisions["objective"] = context.business_objective
        decisions["workflow_version"] = context.workflow_version
        decisions["algorithm_version"] = context.algorithm_version
        
        # Extract simulation decisions
        sim = context.simulation_results
        if sim:
            decisions["simulation"] = {
                "service_level": sim.get("service_level"),
                "cvar_95": sim.get("cvar_95"),
                "tail_risk": sim.get("tail_risk"),
                "status": sim.get("status"),
            }
        
        # Extract backtest decisions
        backtest = context.backtest_results
        if backtest:
            decisions["backtest"] = {
                "best_strategy": backtest.get("best_strategy"),
                "service_level": backtest.get("service_level"),
                "total_cost": backtest.get("total_cost"),
                "status": backtest.get("status"),
            }
        
        # Extract user feedback
        feedback = context.user_feedback
        if feedback:
            decisions["user_feedback"] = {
                "rating": feedback.get("rating"),
                "type": feedback.get("type"),
                "decision": feedback.get("decision"),
            }
        
        # Extract execution metrics
        metrics = context.execution_metrics
        decisions["execution"] = {
            "duration_ms": metrics.get("total_duration_ms"),
            "status": metrics.get("status"),
            "success_rate": metrics.get("success_rate"),
        }
        
        return decisions
    
    def _evaluate_decisions(self, decisions: Dict[str, Any], context: LearningContext) -> List[Dict[str, Any]]:
        """Evaluate decision quality."""
        evaluated = []
        
        # 1. Evaluate simulation decision
        if decisions.get("simulation"):
            sim = decisions["simulation"]
            evaluation = self._evaluate_simulation_decision(sim)
            evaluated.append(evaluation)
        
        # 2. Evaluate backtest decision
        if decisions.get("backtest"):
            backtest = decisions["backtest"]
            evaluation = self._evaluate_backtest_decision(backtest)
            evaluated.append(evaluation)
        
        # 3. Evaluate user feedback
        if decisions.get("user_feedback"):
            feedback = decisions["user_feedback"]
            evaluation = self._evaluate_user_feedback(feedback)
            evaluated.append(evaluation)
        
        # 4. Evaluate execution success
        if decisions.get("execution"):
            execution = decisions["execution"]
            evaluation = self._evaluate_execution_decision(execution)
            evaluated.append(evaluation)
        
        return evaluated
    
    def _evaluate_simulation_decision(self, sim: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate simulation decision quality."""
        score = 0.5
        
        service_level = sim.get("service_level")
        if service_level:
            if 0.9 <= service_level <= 0.99:
                score = 0.9
            elif 0.8 <= service_level < 0.9:
                score = 0.7
            elif service_level < 0.8:
                score = 0.4
        
        tail_risk = sim.get("tail_risk")
        if tail_risk:
            if tail_risk < 0.3:
                score = min(score + 0.1, 1.0)
            elif tail_risk > 0.7:
                score = max(score - 0.2, 0.0)
        
        return {
            "type": "simulation",
            "decision_type": "simulation",
            "score": round(score, 3),
            "service_level": service_level,
            "tail_risk": tail_risk,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _evaluate_backtest_decision(self, backtest: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate backtest decision quality."""
        score = 0.5
        
        service_level = backtest.get("service_level")
        if service_level:
            if service_level >= 0.95:
                score = 0.9
            elif service_level >= 0.85:
                score = 0.7
            else:
                score = 0.4
        
        total_cost = backtest.get("total_cost")
        if total_cost and total_cost > 0:
            # Lower cost is better
            cost_score = 1.0 - min(1.0, total_cost / 10000)
            score = (score + cost_score) / 2
        
        return {
            "type": "backtest",
            "decision_type": "backtest",
            "score": round(score, 3),
            "service_level": service_level,
            "total_cost": total_cost,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _evaluate_user_feedback(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate user feedback quality."""
        rating = feedback.get("rating")
        score = 0.5
        
        if rating:
            if rating >= 4.5:
                score = 0.95
            elif rating >= 4.0:
                score = 0.8
            elif rating >= 3.0:
                score = 0.6
            elif rating >= 2.0:
                score = 0.4
            else:
                score = 0.2
        
        return {
            "type": "user_feedback",
            "decision_type": feedback.get("decision", "unknown"),
            "score": round(score, 3),
            "rating": rating,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _evaluate_execution_decision(self, execution: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate execution decision quality."""
        score = 0.5
        
        status = execution.get("status")
        if status == "completed":
            score = 0.8
        elif status == "failed":
            score = 0.2
        
        success_rate = execution.get("success_rate")
        if success_rate:
            score = (score + success_rate) / 2
        
        return {
            "type": "execution",
            "decision_type": "execution",
            "score": round(score, 3),
            "status": status,
            "success_rate": success_rate,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _update_adaptive_decision(
        self,
        memory: DecisionMemory,
        evaluated: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update Adaptive Decision - DOCUMENT 05 - PART 04 Section 5."""
        updates = {}
        
        if not evaluated:
            return updates
        
        recent_key = f"decision_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        memory.adaptive[recent_key] = {
            "timestamp": datetime.now().isoformat(),
            "evaluations": evaluated,
            "average_score": statistics.mean([e.get("score", 0.5) for e in evaluated]),
        }
        
        updates["new_observation"] = recent_key
        updates["total_observations"] = len(memory.adaptive)
        
        # Apply decay
        self._apply_decay(memory)
        
        return updates
    
    def _update_stable_decision(
        self,
        memory: DecisionMemory,
        evaluated: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update Stable Decision - DOCUMENT 05 - PART 04 Section 5."""
        updates = {}
        
        if memory.confidence < self.confidence_threshold:
            return updates
        
        if len(memory.adaptive) < self.min_observations_for_stable:
            return updates
        
        # Calculate average scores by decision type
        scores_by_type = {}
        for eval_item in evaluated:
            dt = eval_item.get("decision_type", "unknown")
            score = eval_item.get("score", 0.5)
            if dt not in scores_by_type:
                scores_by_type[dt] = []
            scores_by_type[dt].append(score)
        
        for dt, scores in scores_by_type.items():
            if scores:
                avg_score = statistics.mean(scores)
                key = f"{dt}_decision_consistency"
                old = memory.stable.get(key, 0.5)
                new = (old * 0.7) + (avg_score * 0.3)
                memory.stable[key] = round(new, 3)
                updates[key] = {"old": round(old, 3), "new": round(new, 3)}
        
        return updates
    
    def _apply_decay(self, memory: DecisionMemory):
        """Apply knowledge decay to adaptive decision."""
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
    
    def _update_decision_scores(
        self,
        memory: DecisionMemory,
        evaluated: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update Decision Scores - DOCUMENT 05 - PART 04 Section 8."""
        updates = {}
        
        for eval_item in evaluated:
            dt = eval_item.get("decision_type", "unknown")
            score = eval_item.get("score", 0.5)
            
            self.score_manager.add_observation(dt, score)
            new_score = self.score_manager.get_score(dt)
            memory.scores[dt] = new_score
            updates[dt] = new_score
        
        return updates
    
    def _calculate_decision_confidence(
        self,
        memory: DecisionMemory,
        evaluated: List[Dict[str, Any]],
    ) -> float:
        """Calculate Decision Confidence Score - DOCUMENT 05 - PART 04 Section 7."""
        confidence = 0.0
        
        # 1. Historical Coverage
        adaptive_count = len(memory.adaptive)
        if adaptive_count >= 20:
            confidence += 0.3
        elif adaptive_count >= 10:
            confidence += 0.2
        elif adaptive_count >= 5:
            confidence += 0.1
        else:
            confidence += 0.05
        
        # 2. Learning Completeness
        if memory.decision_version >= 10:
            confidence += 0.2
        elif memory.decision_version >= 5:
            confidence += 0.1
        
        # 3. Decision Consistency
        avg_score = statistics.mean([e.get("score", 0.5) for e in evaluated]) if evaluated else 0.5
        confidence += avg_score * 0.15
        
        # 4. Simulation Coverage
        if any(e.get("type") == "simulation" for e in evaluated):
            confidence += 0.15
        
        # 5. Backtest Coverage
        if any(e.get("type") == "backtest" for e in evaluated):
            confidence += 0.1
        
        # 6. Feedback Quality
        if any(e.get("type") == "user_feedback" and e.get("score", 0) > 0.7 for e in evaluated):
            confidence += 0.1
        
        return round(min(1.0, confidence), 3)
    
    def _persist_decisions(
        self,
        context: LearningContext,
        memory: DecisionMemory,
        evaluated: List[Dict[str, Any]],
        confidence: float,
    ) -> List[Dict[str, Any]]:
        """Persist decisions to database."""
        saved_decisions = []
        
        for eval_item in evaluated:
            decision = CompanyAIMemory(
                user_id=context.user_id,
                decision_type=eval_item.get("decision_type", "unknown"),
                decision_input={
                    "context": {
                        "company_id": str(context.company_id),
                        "dataset_id": str(context.dataset_id),
                        "execution_id": str(context.execution_id),
                        "business_objective": context.business_objective,
                    },
                    "evaluation": eval_item,
                },
                decision_output={
                    "score": eval_item.get("score", 0.5),
                    "confidence": confidence,
                    "decision_version": memory.decision_version,
                },
                user_feedback=context.user_feedback.get("type") if context.user_feedback else None,
                confidence_before=memory.confidence,
                confidence_after=confidence,
                created_at=datetime.now(),
            )
            
            self.db.add(decision)
            saved_decisions.append({
                "decision_id": str(decision.id),
                "decision_type": decision.decision_type,
                "score": eval_item.get("score", 0.5),
            })
        
        if saved_decisions:
            self.db.flush()
            logger.info(f"📝 Persisted {len(saved_decisions)} decisions")
        
        return saved_decisions
    
    def _explain_learning(
        self,
        context: LearningContext,
        memory: DecisionMemory,
        adaptive_updates: Dict[str, Any],
        stable_updates: Dict[str, Any],
        score_updates: Dict[str, Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Explain the learning - DOCUMENT 05 - PART 04 Section 10."""
        return {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "confidence_before": memory.confidence,
            "confidence_after": confidence,
            "confidence_change": round(confidence - memory.confidence, 3),
            "adaptive_updates": len(adaptive_updates),
            "stable_updates": len(stable_updates),
            "score_updates": score_updates,
            "decision_version": memory.decision_version,
            "timestamp": datetime.now().isoformat(),
        }