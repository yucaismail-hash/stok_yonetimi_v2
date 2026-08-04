# app/learning/pattern_intelligence.py
"""
Pattern Intelligence Engine - DOCUMENT 05 - PART 03
Learns product and product-group behavioural characteristics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import statistics
import math

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import PatternIntelligence, CompanyLearningMemory


logger = logging.getLogger(__name__)


class PatternMemory:
    """
    Pattern Memory - DOCUMENT 05 - PART 03 Section 6
    
    Contains two independent layers:
    - Stable Pattern: Long-term product behaviour
    - Adaptive Pattern: Recently observed behaviour
    """
    
    def __init__(self, product_id: str):
        self.product_id = product_id
        self.product_group_id: Optional[str] = None
        
        # Stable Pattern - Long-term
        self.stable: Dict[str, Any] = {}
        
        # Adaptive Pattern - Recent
        self.adaptive: Dict[str, Any] = {}
        
        # Confidence
        self.confidence: float = 0.0
        
        # Features
        self.features: Dict[str, Any] = {}
        
        # Version tracking
        self.pattern_version: int = 0
        self.last_updated: Optional[datetime] = None
        self.created_at: Optional[datetime] = None


class PatternFeatureExtractor:
    """
    Pattern Feature Extractor - DOCUMENT 05 - PART 03 Section 7
    Extracts measurable characteristics from historical data.
    """
    
    def extract_features(self, historical_data: List[float]) -> Dict[str, Any]:
        """
        Extract pattern features from historical demand data.
        """
        if not historical_data or len(historical_data) < 4:
            return self._empty_features()
        
        features = {
            "demand_variability": self._calculate_variability(historical_data),
            "demand_stability": self._calculate_stability(historical_data),
            "trend_characteristics": self._calculate_trend(historical_data),
            "seasonality_characteristics": self._calculate_seasonality(historical_data),
            "intermittent_demand": self._calculate_intermittent(historical_data),
            "zero_ratio": self._calculate_zero_ratio(historical_data),
            "mean": statistics.mean(historical_data),
            "std": statistics.stdev(historical_data) if len(historical_data) > 1 else 0,
            "cv": self._calculate_cv(historical_data),
            "min": min(historical_data),
            "max": max(historical_data),
            "range": max(historical_data) - min(historical_data),
            "median": statistics.median(historical_data),
            "sample_count": len(historical_data),
        }
        
        return features
    
    def _empty_features(self) -> Dict[str, Any]:
        """Return empty features for insufficient data."""
        return {
            "demand_variability": 0.0,
            "demand_stability": 0.0,
            "trend_characteristics": "unknown",
            "seasonality_characteristics": "none",
            "intermittent_demand": False,
            "zero_ratio": 0.0,
            "mean": 0.0,
            "std": 0.0,
            "cv": 0.0,
            "min": 0.0,
            "max": 0.0,
            "range": 0.0,
            "median": 0.0,
            "sample_count": 0,
        }
    
    def _calculate_variability(self, data: List[float]) -> float:
        """Calculate demand variability."""
        if not data:
            return 0.0
        mean = statistics.mean(data)
        if mean == 0:
            return 0.0
        std = statistics.stdev(data) if len(data) > 1 else 0
        return std / mean
    
    def _calculate_stability(self, data: List[float]) -> float:
        """Calculate demand stability (1 - variability)."""
        variability = self._calculate_variability(data)
        return max(0, min(1, 1 - variability))
    
    def _calculate_trend(self, data: List[float]) -> str:
        """Calculate trend direction."""
        if len(data) < 4:
            return "unknown"
        
        # Split data into two halves
        mid = len(data) // 2
        first_half = data[:mid]
        second_half = data[mid:]
        
        avg_first = statistics.mean(first_half) if first_half else 0
        avg_second = statistics.mean(second_half) if second_half else 0
        
        if avg_second > avg_first * 1.1:
            return "increasing"
        elif avg_second < avg_first * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_seasonality(self, data: List[float]) -> str:
        """Calculate seasonality characteristic."""
        if len(data) < 12:
            return "none"
        
        # Simple seasonality detection using autocorrelation
        seasonality_score = self._calculate_autocorrelation(data, 12)
        seasonality_score = max(0, min(1, seasonality_score))
        
        if seasonality_score > 0.5:
            return "strong"
        elif seasonality_score > 0.3:
            return "moderate"
        else:
            return "weak"
    
    def _calculate_autocorrelation(self, data: List[float], lag: int) -> float:
        """Calculate autocorrelation at given lag."""
        if len(data) < lag * 2:
            return 0.0
        
        n = len(data) - lag
        mean = statistics.mean(data)
        numerator = 0
        denominator = 0
        
        for i in range(n):
            numerator += (data[i] - mean) * (data[i + lag] - mean)
            denominator += (data[i] - mean) ** 2
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_intermittent(self, data: List[float]) -> bool:
        """Check if demand is intermittent."""
        zero_ratio = self._calculate_zero_ratio(data)
        return zero_ratio > 0.3
    
    def _calculate_zero_ratio(self, data: List[float]) -> float:
        """Calculate ratio of zero values."""
        if not data:
            return 1.0
        zero_count = sum(1 for x in data if x == 0)
        return zero_count / len(data)
    
    def _calculate_cv(self, data: List[float]) -> float:
        """Calculate coefficient of variation."""
        if not data:
            return 0.0
        mean = statistics.mean(data)
        if mean == 0:
            return 0.0
        std = statistics.stdev(data) if len(data) > 1 else 0
        return std / mean


class PatternIntelligenceEngine:
    """
    Pattern Intelligence Engine - DOCUMENT 05 - PART 03
    
    Learns product and product-group behavioural characteristics.
    Depends on Company Learning.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
        self.feature_extractor = PatternFeatureExtractor()
        
        # Memory cache
        self._memories: Dict[str, PatternMemory] = {}
        
        # Configuration
        self.adaptive_window_days = 30
        self.min_observations_for_stable = 5
        self.confidence_threshold = 0.6
    
    def learn(self, context: LearningContext) -> Dict[str, Any]:
        """
        Main learning method - DOCUMENT 05 - PART 03
        
        Learns from execution results and updates Pattern Memory.
        """
        # 1. Get Company Learning first (dependency)
        company_learning = self._get_company_learning(context.company_id)
        
        # 2. Extract SKU-level data
        sku_data = self._extract_sku_data(context)
        
        # 3. Learn patterns for each SKU
        results = []
        for sku, data in sku_data.items():
            pattern_result = self._learn_sku_pattern(
                context,
                sku,
                data,
                company_learning,
            )
            results.append(pattern_result)
        
        # 4. Aggregate to Product Group level
        group_results = self._aggregate_to_product_groups(results)
        
        # 5. Explain the learning
        explanation = self._explain_learning(context, results, group_results)
        
        return {
            "sku_patterns": results,
            "product_group_patterns": group_results,
            "total_skus": len(results),
            "total_groups": len(group_results),
            "explanation": explanation,
        }
    
    def _get_company_learning(self, company_id: UUID) -> Dict[str, Any]:
        """Get Company Learning results (dependency)."""
        learnings = self.repository.get_company_learning(company_id)
        
        company_characteristics = {
            "planning_consistency": 0.5,
            "service_level_preference": 0.95,
            "demand_volatility_factor": 1.0,
        }
        
        for learning in learnings:
            if learning.rule_type == "stable_update":
                data = learning.pattern_data or {}
                key = data.get("key")
                if key == "planning_consistency":
                    company_characteristics["planning_consistency"] = data.get("new_value", 0.5)
                elif key == "service_level_preference":
                    company_characteristics["service_level_preference"] = data.get("new_value", 0.95)
        
        return company_characteristics
    
    def _extract_sku_data(self, context: LearningContext) -> Dict[str, Dict[str, Any]]:
        """Extract SKU-level data from context."""
        sku_data = {}
        
        # Extract from simulation results
        sim = context.simulation_results
        if sim:
            for sku, data in sim.get("results", {}).items():
                if sku not in sku_data:
                    sku_data[sku] = {}
                sku_data[sku]["simulation"] = data
        
        # Extract from backtest results
        backtest = context.backtest_results
        if backtest:
            for sku, data in backtest.get("results", {}).items():
                if sku not in sku_data:
                    sku_data[sku] = {}
                sku_data[sku]["backtest"] = data
        
        # Extract from execution metrics
        metrics = context.execution_metrics
        sku_data["_metadata"] = {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "timestamp": context.triggered_at.isoformat(),
        }
        
        return sku_data
    
    def _learn_sku_pattern(
        self,
        context: LearningContext,
        sku: str,
        data: Dict[str, Any],
        company_learning: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Learn pattern for a single SKU.
        """
        # 1. Get or create pattern memory
        memory = self._get_or_create_memory(sku, context.company_id)
        
        # 2. Extract features from data
        historical_demand = data.get("historical_demand", [])
        features = self.feature_extractor.extract_features(historical_demand)
        
        # 3. Apply Company Learning context
        features = self._apply_company_context(features, company_learning)
        
        # 4. Update Adaptive Pattern
        adaptive_updates = self._update_adaptive_pattern(memory, features, context)
        
        # 5. Update Stable Pattern (if enough confidence)
        stable_updates = self._update_stable_pattern(memory, features)
        
        # 6. Calculate Pattern Confidence
        confidence = self._calculate_pattern_confidence(memory, features)
        memory.confidence = confidence
        
        # 7. Increment pattern version
        memory.pattern_version += 1
        
        # 8. Persist to database
        saved_pattern = self._persist_pattern(
            context,
            sku,
            memory,
            features,
            confidence,
        )
        
        return {
            "sku": sku,
            "features": features,
            "confidence": confidence,
            "pattern_version": memory.pattern_version,
            "adaptive_updates": adaptive_updates,
            "stable_updates": stable_updates,
            "saved_pattern": saved_pattern,
        }
    
    def _get_or_create_memory(self, sku: str, company_id: UUID) -> PatternMemory:
        """Get existing pattern memory or create new."""
        key = f"{company_id}_{sku}"
        if key not in self._memories:
            memory = PatternMemory(sku)
            memory.created_at = datetime.now()
            
            # Cold Start Pattern
            memory.stable = {
                "demand_variability": 0.5,
                "demand_stability": 0.5,
                "trend": "unknown",
                "seasonality": "none",
                "intermittent": False,
                "zero_ratio": 0.0,
            }
            memory.adaptive = {}
            memory.confidence = 0.1
            memory.pattern_version = 0
            memory.last_updated = datetime.now()
            
            self._memories[key] = memory
            
            logger.info(f"🆕 Pattern memory created for SKU: {sku}")
        
        return self._memories[key]
    
    def _apply_company_context(
        self,
        features: Dict[str, Any],
        company_learning: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply Company Learning context to pattern features."""
        # Adjust variability based on company characteristics
        company_volatility = company_learning.get("demand_volatility_factor", 1.0)
        features["adjusted_variability"] = features.get("demand_variability", 0.5) * company_volatility
        
        return features
    
    def _update_adaptive_pattern(
        self,
        memory: PatternMemory,
        features: Dict[str, Any],
        context: LearningContext,
    ) -> Dict[str, Any]:
        """Update Adaptive Pattern with recent observations."""
        updates = {}
        
        # Store recent observation
        recent_key = f"obs_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        memory.adaptive[recent_key] = {
            "timestamp": context.triggered_at.isoformat(),
            "features": features,
            "execution_id": str(context.execution_id),
        }
        
        updates["new_observation"] = recent_key
        updates["total_observations"] = len(memory.adaptive)
        
        # Apply decay
        self._apply_decay(memory)
        
        return updates
    
    def _update_stable_pattern(
        self,
        memory: PatternMemory,
        features: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Update Stable Pattern with consolidated learnings."""
        updates = {}
        
        if memory.confidence < self.confidence_threshold:
            return updates
        
        if len(memory.adaptive) < self.min_observations_for_stable:
            return updates
        
        # Calculate moving averages from adaptive memory
        variability_values = [
            v.get("features", {}).get("demand_variability", 0.5)
            for v in memory.adaptive.values()
            if v.get("features", {}).get("demand_variability") is not None
        ]
        
        if variability_values:
            avg_variability = statistics.mean(variability_values)
            old = memory.stable.get("demand_variability", 0.5)
            new = (old * 0.7) + (avg_variability * 0.3)
            memory.stable["demand_variability"] = round(new, 3)
            memory.stable["demand_stability"] = round(1 - new, 3)
            
            updates["demand_variability"] = {"old": round(old, 3), "new": round(new, 3)}
        
        return updates
    
    def _apply_decay(self, memory: PatternMemory):
        """Apply knowledge decay to adaptive pattern."""
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
    
    def _calculate_pattern_confidence(self, memory: PatternMemory, features: Dict[str, Any]) -> float:
        """Calculate Pattern Confidence Score - DOCUMENT 05 - PART 03 Section 9."""
        confidence = 0.0
        
        # 1. Historical Coverage
        sample_count = features.get("sample_count", 0)
        if sample_count >= 52:
            confidence += 0.3
        elif sample_count >= 26:
            confidence += 0.2
        elif sample_count >= 13:
            confidence += 0.1
        else:
            confidence += 0.05
        
        # 2. Pattern Stability
        stability = features.get("demand_stability", 0.5)
        confidence += stability * 0.2
        
        # 3. Learning Completeness
        adaptive_count = len(memory.adaptive)
        if adaptive_count >= 10:
            confidence += 0.2
        elif adaptive_count >= 5:
            confidence += 0.1
        else:
            confidence += 0.05
        
        # 4. Execution Consistency
        confidence += 0.1
        
        return round(min(1.0, confidence), 3)
    
    def _persist_pattern(
        self,
        context: LearningContext,
        sku: str,
        memory: PatternMemory,
        features: Dict[str, Any],
        confidence: float,
    ) -> Dict[str, Any]:
        """Persist pattern to database."""
        pattern = PatternIntelligence(
            user_id=context.user_id,
            product_group_id=None,
            pattern_type=self._determine_pattern_type(features),
            pattern_params={
                "sku": sku,
                "features": features,
                "stable": memory.stable,
                "adaptive": list(memory.adaptive.keys())[-10:],
                "pattern_version": memory.pattern_version,
            },
            confidence_score=confidence,
            is_active=True,
            last_calculated_at=datetime.now(),
        )
        
        self.db.add(pattern)
        self.db.flush()
        
        return {
            "pattern_id": str(pattern.id),
            "pattern_type": pattern.pattern_type,
            "confidence": confidence,
        }
    
    def _determine_pattern_type(self, features: Dict[str, Any]) -> str:
        """Determine pattern type from features."""
        variability = features.get("demand_variability", 0.5)
        intermittent = features.get("intermittent_demand", False)
        seasonality = features.get("seasonality_characteristics", "none")
        trend = features.get("trend_characteristics", "unknown")
        
        if intermittent:
            return "intermittent"
        elif seasonality in ["strong", "moderate"]:
            return "seasonal"
        elif trend in ["increasing", "decreasing"]:
            return "trend"
        elif variability < 0.3:
            return "stable"
        else:
            return "volatile"
    
    def _aggregate_to_product_groups(self, sku_patterns: List[Dict]) -> List[Dict[str, Any]]:
        """Aggregate SKU patterns to product group level."""
        # Simple aggregation - average of all SKUs
        if not sku_patterns:
            return []
        
        groups = {}
        for pattern in sku_patterns:
            group = pattern.get("product_group", "default")
            if group not in groups:
                groups[group] = []
            groups[group].append(pattern)
        
        aggregated = []
        for group, patterns in groups.items():
            avg_confidence = statistics.mean([p.get("confidence", 0) for p in patterns])
            avg_variability = statistics.mean([
                p.get("features", {}).get("demand_variability", 0.5)
                for p in patterns
            ])
            
            aggregated.append({
                "group": group,
                "sku_count": len(patterns),
                "avg_confidence": round(avg_confidence, 3),
                "avg_variability": round(avg_variability, 3),
                "patterns": patterns,
            })
        
        return aggregated
    
    def _explain_learning(
        self,
        context: LearningContext,
        sku_patterns: List[Dict],
        group_patterns: List[Dict],
    ) -> Dict[str, Any]:
        """Explain pattern learning - DOCUMENT 05 - PART 03 Section 12."""
        return {
            "execution_id": str(context.execution_id),
            "business_objective": context.business_objective,
            "skus_learned": len(sku_patterns),
            "groups_learned": len(group_patterns),
            "timestamp": datetime.now().isoformat(),
            "total_patterns": len(sku_patterns) + len(group_patterns),
        }