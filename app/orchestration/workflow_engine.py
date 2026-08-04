# app/orchestration/workflow_engine.py
"""
Workflow Orchestration Engine
DOCUMENT 01 - Workflow Principle
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import uuid
import logging
from enum import Enum

from sqlalchemy.orm import Session

from app.models.workflow import WorkflowExecution, WorkflowTask
from app.models.dataset import Dataset
from app.models.company import User
from app.models.execution import ExecutionResult

from app.orchestration.objectives import (
    ObjectiveType, 
    BusinessObjective, 
    get_objective, 
    list_objectives,
    WorkflowStep,
)
from app.orchestration.dependency_manager import DependencyManager

# Internal API çağrıları için (sonraki adımda implemente edilecek)
from app.services.execution.internal_api import InternalAPIClient

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Bazı enrichment'ler atlandı


class WorkflowEngine:
    """
    Workflow Orchestration Engine.
    
    Kullanıcı hedeflerini alır, gerekli analiz zincirini oluşturur,
    bağımlılıkları yönetir ve çalıştırır.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.internal_api = InternalAPIClient()
    
    def list_objectives(self) -> List[Dict[str, Any]]:
        """Tüm iş hedeflerini listele."""
        return list_objectives()
    
    def get_objective(self, objective_type: str) -> Optional[Dict[str, Any]]:
        """İş hedefini getir."""
        try:
            obj_type = ObjectiveType(objective_type)
            objective = get_objective(obj_type)
            if objective:
                return {
                    "type": objective.objective_type.value,
                    "name": objective.name,
                    "description": objective.description,
                    "steps": [
                        {
                            "step_type": s.step_type,
                            "is_functional": s.is_functional,
                            "depends_on": s.depends_on,
                            "can_skip": s.can_skip,
                        }
                        for s in objective.steps
                    ]
                }
        except ValueError:
            pass
        return None
    
    def run_workflow(
        self,
        objective_type: str,
        dataset_id: int,
        user_id: int,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Workflow'u çalıştır.
        
        Args:
            objective_type: İş hedefi tipi
            dataset_id: Dataset ID
            user_id: Kullanıcı ID
            params: Ek parametreler
        
        Returns:
            Workflow execution result
        """
        # 1. Objective'i kontrol et
        try:
            obj_type = ObjectiveType(objective_type)
        except ValueError:
            return {
                "status": "failed",
                "error": f"Unknown objective_type: {objective_type}",
                "available_objectives": [o.value for o in ObjectiveType]
            }
        
        objective = get_objective(obj_type)
        if not objective:
            return {
                "status": "failed",
                "error": f"Objective not found: {objective_type}"
            }
        
        # 2. Dataset'i kontrol et
        dataset = self.db.query(Dataset).filter(
            Dataset.id == dataset_id,
            Dataset.user_id == user_id,
            Dataset.is_active == True,
            Dataset.state == "approved"  # Sadece onaylanmış dataset'ler
        ).first()
        
        if not dataset:
            return {
                "status": "failed",
                "error": f"Dataset {dataset_id} not found or not approved",
                "dataset_id": dataset_id
            }
        
        # 3. Workflow oluştur
        workflow_id = str(uuid.uuid4())
        
        workflow = WorkflowExecution(
            user_id=user_id,
            dataset_id=dataset_id,
            objective_type=objective_type,
            objective_params=params or {},
            status=WorkflowStatus.PENDING.value,
            workflow_id=workflow_id,
            functional_dependencies=objective.get_functional_steps(),
            enrichment_dependencies=objective.get_enrichment_steps(),
        )
        
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        
        logger.info(f"🚀 Workflow {workflow_id} started for objective: {objective_type}")
        
        # 4. Workflow'u çalıştır
        try:
            result = self._execute_workflow(workflow, objective, dataset)
            
            # Workflow'u güncelle
            workflow.status = result["status"]
            workflow.completed_at = datetime.now()
            workflow.progress = 100
            workflow.final_result = result
            
            self.db.add(workflow)
            self.db.commit()
            
            logger.info(f"✅ Workflow {workflow_id} completed with status: {result['status']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Workflow {workflow_id} failed: {str(e)}")
            
            workflow.status = WorkflowStatus.FAILED.value
            workflow.error_message = str(e)
            self.db.add(workflow)
            self.db.commit()
            
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "objective": objective_type,
                "dataset_id": dataset_id,
            }
    
    def _execute_workflow(
        self,
        workflow: WorkflowExecution,
        objective: BusinessObjective,
        dataset: Dataset,
    ) -> Dict[str, Any]:
        """
        Workflow'u adım adım çalıştır.
        """
        # 1. Bağımlılıkları kontrol et
        dependency_manager = DependencyManager(objective)
        
        # Mevcut tüm analiz modüllerini kontrol et (gerçekte availability kontrolü yapılır)
        available_steps = self._get_available_steps(objective)
        
        validation = dependency_manager.validate_workflow(available_steps)
        
        if not validation["is_valid"]:
            return {
                "status": "failed",
                "error": "Missing functional dependencies",
                "missing_functional": validation["functional_missing"],
                "validation": validation,
            }
        
        # 2. Çalıştırma sırasını belirle
        execution_order = validation["execution_order"]
        skipped_steps = validation["enrichment_skipped"]
        
        # 3. Adımları çalıştır
        results = {}
        step_results = []
        has_error = False
        
        for step_type in execution_order:
            # Skip kontrolü
            if step_type in skipped_steps:
                logger.info(f"⏭️ Skipping enrichment step: {step_type}")
                step_results.append({
                    "step": step_type,
                    "status": "skipped",
                    "message": "Enrichment skipped due to missing data"
                })
                continue
            
            # Step'i çalıştır
            step = dependency_manager.step_map[step_type]
            
            try:
                step_result = self._execute_step(
                    step_type=step_type,
                    step=step,
                    dataset=dataset,
                    workflow=workflow,
                    previous_results=results,
                )
                
                results[step_type] = step_result
                step_results.append({
                    "step": step_type,
                    "status": "completed",
                    "result": step_result,
                })
                
                # Task oluştur
                task = WorkflowTask(
                    workflow_id=workflow.id,
                    task_type=step_type,
                    task_order=len(step_results),
                    depends_on=step.depends_on,
                    is_functional=step.is_functional,
                    status="completed",
                    result_data=step_result,
                    completed_at=datetime.now(),
                )
                self.db.add(task)
                
                # Workflow progress'i güncelle
                workflow.current_stage = step_type
                workflow.progress = int((len(step_results) / len(execution_order)) * 100)
                self.db.add(workflow)
                self.db.commit()
                
            except Exception as e:
                logger.error(f"❌ Step {step_type} failed: {str(e)}")
                
                if step.is_functional:
                    # Functional step başarısız - workflow durur
                    has_error = True
                    step_results.append({
                        "step": step_type,
                        "status": "failed",
                        "error": str(e),
                    })
                    
                    # Task'i kaydet
                    task = WorkflowTask(
                        workflow_id=workflow.id,
                        task_type=step_type,
                        task_order=len(step_results),
                        depends_on=step.depends_on,
                        is_functional=step.is_functional,
                        status="failed",
                        error_message=str(e),
                    )
                    self.db.add(task)
                    self.db.commit()
                    
                    break
                else:
                    # Enrichment step başarısız - devam et
                    logger.warning(f"⚠️ Enrichment {step_type} failed but continuing")
                    step_results.append({
                        "step": step_type,
                        "status": "failed_continued",
                        "error": str(e),
                    })
                    
                    results[step_type] = {"error": str(e)}
        
        # 4. AI Decision (DOCUMENT 01 - AI Architecture)
        ai_decision = self._generate_ai_decision(results, objective, dataset)
        
        # 5. Sonucu oluştur
        return {
            "workflow_id": workflow.workflow_id,
            "objective": objective.objective_type.value,
            "dataset_id": dataset.id,
            "status": "failed" if has_error else "completed",
            "steps": step_results,
            "results": results,
            "ai_decision": ai_decision,
            "skipped_enrichments": skipped_steps,
            "execution_time": datetime.now().isoformat(),
        }
    
    def _execute_step(
        self,
        step_type: str,
        step: WorkflowStep,
        dataset: Dataset,
        workflow: WorkflowExecution,
        previous_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Tek bir step'i çalıştır.
        Internal API'yi çağırır.
        """
        logger.info(f"⚙️ Executing step: {step_type}")
        
        # Internal API çağrısı
        try:
            result = self.internal_api.call(
                endpoint=f"/internal/{step_type}",
                method="POST",
                data={
                    "dataset_id": dataset.id,
                    "user_id": workflow.user_id,
                    "workflow_id": workflow.workflow_id,
                    "params": step.params,
                    "previous_results": previous_results,
                }
            )
            return result
        except Exception as e:
            logger.error(f"❌ Internal API call failed for {step_type}: {str(e)}")
            raise
    
    def _get_available_steps(self, objective: BusinessObjective) -> Set[str]:
        """
        Mevcut analiz modüllerini kontrol et.
        Gerçekte servis availability kontrolü yapılır.
        """
        # Şimdilik tüm modüller mevcut varsayalım
        return {s.step_type for s in objective.steps}
    
    def _generate_ai_decision(
        self,
        results: Dict[str, Any],
        objective: BusinessObjective,
        dataset: Dataset,
    ) -> Dict[str, Any]:
        """
        AI Decision Engine - DOCUMENT 01
        Analiz sonuçlarını tüketir ve iş kararı üretir.
        """
        # ADIM 6'da detaylandırılacak
        # Şimdilik basit bir özet
        return {
            "summary": f"AI Decision for {objective.objective_type.value}",
            "recommendations": [
                "Analiz sonuçlarına göre öneriler burada olacak"
            ],
            "confidence_score": 0.85,
            "requires_human_approval": True,
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        Workflow durumunu getir.
        """
        workflow = self.db.query(WorkflowExecution).filter(
            WorkflowExecution.workflow_id == workflow_id
        ).first()
        
        if not workflow:
            return None
        
        tasks = self.db.query(WorkflowTask).filter(
            WorkflowTask.workflow_id == workflow.id
        ).order_by(WorkflowTask.task_order).all()
        
        return {
            "workflow_id": workflow.workflow_id,
            "objective_type": workflow.objective_type,
            "status": workflow.status,
            "progress": workflow.progress,
            "current_stage": workflow.current_stage,
            "started_at": workflow.created_at,
            "completed_at": workflow.completed_at,
            "tasks": [
                {
                    "task_type": t.task_type,
                    "status": t.status,
                    "is_functional": t.is_functional,
                    "duration_ms": t.duration_ms,
                    "error": t.error_message,
                }
                for t in tasks
            ],
            "final_result": workflow.final_result,
        }