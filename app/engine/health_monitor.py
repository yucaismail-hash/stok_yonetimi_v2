# app/engine/intelligence/health_monitor.py
"""
Health Monitor - DOCUMENT 04 - PART 05
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.engine.intelligence.models import HealthMetrics
from app.engine.worker_manager import WorkerManager


logger = logging.getLogger(__name__)


class HealthMonitor:
    """
    Health Monitor - DOCUMENT 04 Section 11
    
    Continuously monitors execution health.
    """
    
    def __init__(self, worker_manager: WorkerManager):
        self.worker_manager = worker_manager
        self._health_history: List[HealthMetrics] = []
        self._current_health: Optional[HealthMetrics] = None
    
    def collect_metrics(
        self,
        queue_length: int = 0,
        cpu_usage: float = 0.0,
        memory_usage: float = 0.0,
    ) -> HealthMetrics:
        """Collect health metrics."""
        worker_stats = self.worker_manager.get_worker_stats()
        
        # Calculate worker availability
        total_workers = worker_stats.get("total", 0)
        available = worker_stats.get("available", 0)
        worker_availability = available / total_workers if total_workers > 0 else 0
        
        # Calculate success rate from recent executions
        success_rate = self._calculate_success_rate()
        
        # Calculate health score
        health_score = self._calculate_health_score(
            worker_availability=worker_availability,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            success_rate=success_rate,
        )
        
        metrics = HealthMetrics(
            queue_length=queue_length,
            worker_availability=worker_availability,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            execution_success_rate=success_rate,
            retry_rate=worker_stats.get("retry_rate", 0),
            failure_rate=1 - success_rate,
            avg_duration_ms=self._get_avg_duration(),
            health_score=health_score,
            timestamp=datetime.now(),
        )
        
        self._current_health = metrics
        self._health_history.append(metrics)
        
        # Keep history limited
        if len(self._health_history) > 100:
            self._health_history = self._health_history[-100:]
        
        return metrics
    
    def get_current_health(self) -> Optional[HealthMetrics]:
        """Get current health metrics."""
        return self._current_health
    
    def get_health_history(self, limit: int = 100) -> List[HealthMetrics]:
        """Get health history."""
        return self._health_history[-limit:]
    
    def _calculate_success_rate(self) -> float:
        """Calculate execution success rate."""
        # Placeholder - actual implementation will query execution history
        return 0.95
    
    def _calculate_health_score(
        self,
        worker_availability: float,
        cpu_usage: float,
        memory_usage: float,
        success_rate: float,
    ) -> float:
        """Calculate overall health score."""
        # Normalize to 0-100
        availability_score = worker_availability * 30
        cpu_score = max(0, (100 - cpu_usage) / 100 * 25)
        memory_score = max(0, (100 - memory_usage) / 100 * 20)
        success_score = success_rate * 25
        
        return round(availability_score + cpu_score + memory_score + success_score, 2)
    
    def _get_avg_duration(self) -> Optional[float]:
        """Get average execution duration."""
        # Placeholder - actual implementation will query execution history
        return 45000