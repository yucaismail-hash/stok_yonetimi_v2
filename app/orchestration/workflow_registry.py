# app/orchestration/workflow_registry.py
"""
Workflow Registry
Çalışan workflow'ları takip eder.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """
    Workflow kayıt defteri.
    Çalışan workflow'ları ve durumlarını takip eder.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._workflows: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def register(self, workflow_id: str, objective_type: str, dataset_id: int, user_id: int) -> str:
        """Workflow'u kaydet."""
        with self._lock:
            self._workflows[workflow_id] = {
                "workflow_id": workflow_id,
                "objective_type": objective_type,
                "dataset_id": dataset_id,
                "user_id": user_id,
                "status": "pending",
                "progress": 0,
                "started_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            logger.info(f"📝 Workflow registered: {workflow_id}")
            return workflow_id
    
    def update(self, workflow_id: str, status: str, progress: int, result: Optional[Dict] = None):
        """Workflow durumunu güncelle."""
        with self._lock:
            if workflow_id in self._workflows:
                self._workflows[workflow_id]["status"] = status
                self._workflows[workflow_id]["progress"] = progress
                self._workflows[workflow_id]["updated_at"] = datetime.now().isoformat()
                if result:
                    self._workflows[workflow_id]["result"] = result
    
    def get(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Workflow bilgisini getir."""
        with self._lock:
            return self._workflows.get(workflow_id)
    
    def list(self, user_id: Optional[int] = None) -> Dict[str, Dict[str, Any]]:
        """Tüm workflow'ları listele."""
        with self._lock:
            if user_id:
                return {
                    wf_id: wf 
                    for wf_id, wf in self._workflows.items() 
                    if wf["user_id"] == user_id
                }
            return self._workflows.copy()