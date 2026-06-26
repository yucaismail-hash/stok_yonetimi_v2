from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from app.database import get_db
from app.models import User, AnalysisResult
from app.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])

class TaskResponse(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int
    message: str
    created_at: datetime
    total_materials: int
    completed_materials: int
    result_type: str

@router.get("/async")
async def get_async_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Kullanıcının tüm async görevlerini listele"""
    tasks = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.result_type == 'forecast_batch_async'
    ).order_by(AnalysisResult.created_at.desc()).limit(limit).all()
    
    result = []
    for task in tasks:
        data = task.data if isinstance(task.data, dict) else {}
        
        # ✅ status kontrolü - data içinden al
        task_status = data.get('status', 'processing')
        total = data.get('total', 0)
        results = data.get('results', [])
        completed = len(results)
        progress = data.get('progress', 0)
        
        # ✅ progress hesapla
        if task_status == 'completed':
            progress = 100
        elif progress == 0 and total > 0:
            progress = min(95, int((completed / max(total, 1)) * 100))
        
        # ✅ Rapor adı
        report_names = {
            'forecast_batch_async': '📈 Talep Tahmini',
            'pattern_batch_async': '📊 Talep Paterni',
            'safety_stock_batch_async': '🛡️ Emniyet Stoğu',
            'simulation_batch_async': '🎲 Monte Carlo Simülasyonu',
            'backtest_batch_async': '📉 Backtest Analizi',
        }
        report_name = report_names.get(task.result_type, '📊 Analiz Raporu')
        
        result.append({
            'task_id': task.task_id or f"legacy_{task.id}",
            'status': task_status,
            'progress': progress,
            'message': data.get('message', 'Tamamlandı!' if task_status == 'completed' else 'İşleniyor...'),
            'created_at': task.created_at,
            'total_materials': total,
            'completed_materials': completed,
            'result_type': task.result_type,
            'report_name': report_name
        }) 
    
    return {"success": True, "tasks": result}


@router.get("/async/{task_id}")
async def get_async_task_detail(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Belirli bir görevin detaylarını getir"""
    task = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.task_id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    
    data = task.data if isinstance(task.data, dict) else {}
    
    return {
        "success": True,
        "task": {
            "task_id": task.task_id,
            "status": "completed" if data.get('status') == 'completed' else 'processing',
            "progress": 100 if data.get('status') == 'completed' else 50,
            "message": data.get('message', 'Tamamlandı!' if data.get('status') == 'completed' else 'İşleniyor...'),
            "created_at": task.created_at,
            "total_materials": data.get('total', 0),
            "results": data.get('results', [])
        }
    }


@router.delete("/async/{task_id}")
async def delete_async_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bir görevi sil"""
    task = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.task_id == task_id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    
    db.delete(task)
    db.commit()
    
    return {"success": True, "message": "Görev silindi"}
