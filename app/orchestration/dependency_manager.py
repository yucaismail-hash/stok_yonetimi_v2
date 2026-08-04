# app/orchestration/dependency_manager.py
"""
Dependency Manager
DOCUMENT 01 - Dependency Rules
"""

from typing import List, Dict, Any, Optional, Set
from collections import defaultdict, deque
import logging

from app.orchestration.objectives import WorkflowStep, BusinessObjective

logger = logging.getLogger(__name__)


class DependencyManager:
    """
    Workflow dependency manager.
    
    - Functional Dependency: Required, execution stops if missing
    - Enrichment Dependency: Optional, execution continues
    """
    
    def __init__(self, objective: BusinessObjective):
        self.objective = objective
        self.step_map = {s.step_type: s for s in objective.steps}
        self.dependency_graph = self._build_graph()
    
    def _build_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph."""
        graph = defaultdict(list)
        for step in self.objective.steps:
            for dep in step.depends_on:
                graph[dep].append(step.step_type)
        return dict(graph)
    
    def get_execution_order(self) -> List[str]:
        """
        Topological sort ile çalıştırma sırasını belirle.
        """
        # Tüm step'leri al
        all_steps = set(self.step_map.keys())
        visited = set()
        order = []
        
        def dfs(step: str):
            if step in visited:
                return
            visited.add(step)
            
            # Bağımlılıkları önce ekle
            for dep in self.step_map[step].depends_on:
                if dep in all_steps and dep not in visited:
                    dfs(dep)
            
            order.append(step)
        
        for step in all_steps:
            if step not in visited:
                dfs(step)
        
        return order
    
    def get_functional_dependencies(self) -> List[str]:
        """Get all functional dependencies."""
        return [s.step_type for s in self.objective.steps if s.is_functional]
    
    def get_enrichment_dependencies(self) -> List[str]:
        """Get all enrichment dependencies."""
        return [s.step_type for s in self.objective.steps if not s.is_functional]
    
    def check_dependencies(self, available_steps: Set[str]) -> Dict[str, Any]:
        """
        Mevcut step'lere göre bağımlılıkları kontrol et.
        
        Returns:
            {
                "functional": {
                    "available": [...],
                    "missing": [...],
                    "can_execute": bool
                },
                "enrichment": {
                    "available": [...],
                    "missing": [...],
                    "will_skip": [...]
                }
            }
        """
        functional_steps = self.get_functional_dependencies()
        enrichment_steps = self.get_enrichment_dependencies()
        
        # Functional kontrol
        functional_available = [s for s in functional_steps if s in available_steps]
        functional_missing = [s for s in functional_steps if s not in available_steps]
        can_execute = len(functional_missing) == 0
        
        # Enrichment kontrol
        enrichment_available = [s for s in enrichment_steps if s in available_steps]
        enrichment_missing = [s for s in enrichment_steps if s not in available_steps]
        will_skip = [s for s in enrichment_missing if self.step_map[s].can_skip]
        cannot_skip = [s for s in enrichment_missing if not self.step_map[s].can_skip]
        
        return {
            "functional": {
                "available": functional_available,
                "missing": functional_missing,
                "can_execute": can_execute,
            },
            "enrichment": {
                "available": enrichment_available,
                "missing": enrichment_missing,
                "will_skip": will_skip,
                "cannot_skip": cannot_skip,
            },
            "can_execute": can_execute and len(cannot_skip) == 0,
        }
    
    def get_skipped_steps(self, available_steps: Set[str]) -> List[str]:
        """
        Eksik olduğu için atlanacak enrichment step'ler.
        """
        enrichment_steps = self.get_enrichment_dependencies()
        return [s for s in enrichment_steps if s not in available_steps and self.step_map[s].can_skip]
    
    def validate_workflow(self, available_steps: Set[str]) -> Dict[str, Any]:
        """
        Workflow'un çalışabilirliğini doğrula.
        """
        dependency_check = self.check_dependencies(available_steps)
        
        return {
            "is_valid": dependency_check["can_execute"],
            "functional_available": dependency_check["functional"]["available"],
            "functional_missing": dependency_check["functional"]["missing"],
            "enrichment_available": dependency_check["enrichment"]["available"],
            "enrichment_skipped": dependency_check["enrichment"]["will_skip"],
            "execution_order": self.get_execution_order(),
            "can_skip_enrichments": len(dependency_check["enrichment"]["will_skip"]) > 0,
        }