# app/api/v2/endpoints/decision.py
"""
Decision API Endpoints
DOCUMENT 01 - Workflow Principle
DOCUMENT 01 - AI Architecture
"""

from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.company import User
from app.models.dataset import Dataset
from app.models.workflow import WorkflowExecution, WorkflowTask
from app.models.execution import ExecutionResult

from app.orchestration import WorkflowEngine
from app.services.ai import AIDecisionEngine, get_provider_manager

from app.schemas.decision import (
    DecisionRunRequest,
    DecisionRunResponse,
    DecisionStatusResponse,
    ObjectiveListResponse,
    DecisionTaskStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# 1. OBJECTIVES - İş Hedeflerini Listele
# ============================================

@router.get("/objectives")
async def list_objectives(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ObjectiveListResponse:
    """
    Tüm iş hedeflerini listele.
    """
    engine = WorkflowEngine(db)
    objectives = engine.list_objectives()
    
    return ObjectiveListResponse(
        total=len(objectives),
        objectives=objectives,
        message=f"{len(objectives)} objectives available"
    )


@router.get("/objectives/{objective_type}")
async def get_objective(
    objective_type: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    İş hedefi detayını getir.
    """
    engine = WorkflowEngine(db)
    objective = engine.get_objective(objective_type)
    
    if not objective:
        raise HTTPException(
            status_code=404,
            detail=f"Objective '{objective_type}' not found"
        )
    
    return objective


# ============================================
# 2. RUN - İş Hedefini Çalıştır
# ============================================

@router.post("/run")
async def run_decision(
    request: DecisionRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionRunResponse:
    """
    İş hedefini çalıştır.
    Kullanıcı iş hedefini seçer, platform otomatik olarak workflow'u oluşturur.
    """
    # 1. Dataset kontrolü
    dataset = db.query(Dataset).filter(
        Dataset.id == request.dataset_id,
        Dataset.user_id == current_user.id,
        Dataset.is_active == True,
        Dataset.state == "approved"
    ).first()
    
    if not dataset:
        raise HTTPException(
            status_code=404,
            detail=f"Dataset {request.dataset_id} not found or not approved"
        )
    
    # 2. Workflow ID oluştur
    workflow_id = str(uuid.uuid4())
    
    # 3. Workflow execution kaydı oluştur
    workflow = WorkflowExecution(
        user_id=current_user.id,
        dataset_id=request.dataset_id,
        objective_type=request.objective_type,
        objective_params=request.params or {},
        status="pending",
        workflow_id=workflow_id,
        progress=0,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    
    # 4. Background task olarak çalıştır
    background_tasks.add_task(
        _run_workflow_with_ai,
        workflow_id=workflow_id,
        workflow_db_id=workflow.id,
        objective_type=request.objective_type,
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        user_email=current_user.email,
        params=request.params or {},
        language=request.language or "Türkçe",
        db=db,
    )
    
    return DecisionRunResponse(
        workflow_id=workflow_id,
        objective_type=request.objective_type,
        dataset_id=request.dataset_id,
        status="pending",
        message="Workflow started successfully",
        status_url=f"/api/v2/decision/status/{workflow_id}"
    )


# ============================================
# 3. STATUS - Workflow Durumu
# ============================================

@router.get("/status/{workflow_id}")
async def get_decision_status(
    workflow_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DecisionStatusResponse:
    """
    Karar çalıştırma durumunu getir.
    """
    workflow = db.query(WorkflowExecution).filter(
        WorkflowExecution.workflow_id == workflow_id,
        WorkflowExecution.user_id == current_user.id
    ).first()
    
    if not workflow:
        raise HTTPException(
            status_code=404,
            detail=f"Workflow {workflow_id} not found"
        )
    
    tasks = db.query(WorkflowTask).filter(
        WorkflowTask.workflow_id == workflow.id
    ).order_by(WorkflowTask.task_order).all()
    
    execution = db.query(ExecutionResult).filter(
        ExecutionResult.workflow_id == workflow_id
    ).first()
    
    ai_decision = execution.ai_summary if execution else None
    
    return DecisionStatusResponse(
        workflow_id=workflow.workflow_id,
        objective_type=workflow.objective_type,
        status=workflow.status,
        progress=workflow.progress or 0,
        current_stage=workflow.current_stage,
        started_at=workflow.created_at.isoformat() if workflow.created_at else None,
        completed_at=workflow.completed_at.isoformat() if workflow.completed_at else None,
        tasks=[
            DecisionTaskStatus(
                task_type=t.task_type,
                status=t.status,
                is_functional=t.is_functional,
                duration_ms=t.duration_ms,
                error=t.error_message,
            )
            for t in tasks
        ],
        result=workflow.final_result,
        ai_decision=ai_decision,
        error=workflow.error_message,
    )


# ============================================
# 4. AI Health - Provider Sağlık Kontrolü
# ============================================

@router.get("/ai/health")
async def ai_health_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    AI provider'ların sağlık durumunu kontrol et.
    """
    provider_manager = get_provider_manager()
    stats = provider_manager.get_stats()
    health = provider_manager.health_check_all()
    
    return {
        "provider_stats": stats,
        "provider_health": health,
        "active_provider": provider_manager._active_provider,
        "available_providers": provider_manager.get_available_providers(),
    }


# ============================================
# 5. BACKGROUND TASK - Workflow Çalıştırıcı
# ============================================

async def _run_workflow_with_ai(
    workflow_id: str,
    workflow_db_id: int,
    objective_type: str,
    dataset_id: int,
    user_id: int,
    user_email: str,
    params: Dict[str, Any],
    language: str,
    db: Session,
):
    """
    Workflow'u çalıştır ve AI kararı üret.
    """
    try:
        # 1. Workflow engine
        engine = WorkflowEngine(db)
        result = engine.run_workflow(
            objective_type=objective_type,
            dataset_id=dataset_id,
            user_id=user_id,
            params=params,
        )
        
        # 2. Workflow'u güncelle
        workflow = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == workflow_db_id
        ).first()
        
        if workflow:
            workflow.status = result.get("status", "completed")
            workflow.progress = 100
            workflow.completed_at = datetime.now()
            workflow.final_result = result
            db.add(workflow)
            db.commit()
        
        # 3. AI Decision (sadece başarılı ise)
        if result.get("status") in ["completed", "partial"]:
            ai_engine = AIDecisionEngine(language=language)
            
            ai_result = ai_engine.generate_decision(
                analysis_type=objective_type,
                analysis_data=result.get("results", {}),
                material_data=params.get("material_data"),
            )
            
            # 4. Execution Result'a kaydet
            execution = ExecutionResult(
                user_id=user_id,
                dataset_id=dataset_id,
                objective_type=objective_type,
                workflow_id=workflow_id,
                task_id=str(uuid.uuid4()),
                result_type=objective_type,
                result_data=result.get("results", {}),
                params=params,
                status="completed" if ai_result.get("is_fallback") else "completed",
                progress=100,
                total_materials=result.get("results", {}).get("total_items", 0),
                processed_count=result.get("results", {}).get("total_items", 0),
                ai_summary=ai_result,
                ai_status="completed" if not ai_result.get("is_fallback") else "fallback",
                ai_version="1.0",
                ai_created_at=datetime.now(),
                ai_prompt_version="1.0",
            )
            db.add(execution)
            db.commit()
            
            logger.info(f"✅ AI Decision generated for workflow: {workflow_id}")
            logger.info(f"   Decision: {ai_result.get('decision')}")
            logger.info(f"   Priority: {ai_result.get('priority')}")
            logger.info(f"   Confidence: {ai_result.get('confidence')}")
        
    except Exception as e:
        logger.error(f"❌ Workflow {workflow_id} failed: {str(e)}")
        
        workflow = db.query(WorkflowExecution).filter(
            WorkflowExecution.id == workflow_db_id
        ).first()
        
        if workflow:
            workflow.status = "failed"
            workflow.error_message = str(e)
            db.add(workflow)
            db.commit()