# app/services/ai/ai_summary_engine.py
"""
AI Summary Engine
Stores and retrieves AI summaries.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

from sqlalchemy.orm import Session

from app.models.execution import ExecutionResult

logger = logging.getLogger(__name__)


class AISummaryEngine:
    """
    AI Summary Engine.
    
    AI özetlerini yönetir:
    - Kaydetme
    - Getirme
    - Versiyonlama
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save_summary(
        self,
        workflow_id: str,
        objective: str,
        summary: str,
        decisions: str,
        action_plan: Optional[str] = None,
        provider: str = "unknown",
    ) -> Optional[ExecutionResult]:
        """
        AI özetini kaydet.
        """
        execution = self.db.query(ExecutionResult).filter(
            ExecutionResult.workflow_id == workflow_id
        ).first()
        
        if not execution:
            logger.warning(f"Execution result not found for workflow: {workflow_id}")
            return None
        
        # AI summary'yi güncelle
        execution.ai_summary = {
            "objective": objective,
            "summary": summary,
            "decisions": decisions,
            "action_plan": action_plan,
            "provider": provider,
            "generated_at": datetime.now().isoformat(),
        }
        execution.ai_status = "completed"
        execution.ai_created_at = datetime.now()
        execution.ai_version = "1.0"
        
        self.db.add(execution)
        self.db.commit()
        self.db.refresh(execution)
        
        logger.info(f"✅ AI Summary saved for workflow: {workflow_id}")
        
        return execution
    
    def get_summary(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        AI özetini getir.
        """
        execution = self.db.query(ExecutionResult).filter(
            ExecutionResult.workflow_id == workflow_id
        ).first()
        
        if not execution:
            return None
        
        return {
            "workflow_id": workflow_id,
            "objective": execution.objective_type,
            "summary": execution.ai_summary,
            "status": execution.ai_status,
            "version": execution.ai_version,
            "created_at": execution.ai_created_at,
        }
    
    def get_all_summaries(self, user_id: int, limit: int = 10) -> list:
        """
        Kullanıcının tüm AI özetlerini getir.
        """
        executions = self.db.query(ExecutionResult).filter(
            ExecutionResult.user_id == user_id,
            ExecutionResult.ai_summary.isnot(None)
        ).order_by(
            ExecutionResult.ai_created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "workflow_id": e.workflow_id,
                "objective": e.objective_type,
                "summary": e.ai_summary,
                "status": e.ai_status,
                "created_at": e.ai_created_at,
            }
            for e in executions
        ]