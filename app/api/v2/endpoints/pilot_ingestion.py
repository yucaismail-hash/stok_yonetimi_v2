from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from typing import Optional
from sqlalchemy.orm import Session

from app.application.canonical_excel_ingestion import CanonicalExcelError, CanonicalExcelIngestionService, template_bytes
from app.auth import get_current_user
from app.database import get_db
from app.schemas.pilot_dataset import CurrentPilotDatasetResponse

router = APIRouter()

@router.get('/pilot/current', response_model=Optional[CurrentPilotDatasetResponse])
def get_current_pilot_dataset(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return CanonicalExcelIngestionService().get_current_accepted(db, current_user.company_id)

@router.get('/pilot/template')
def download_template(current_user=Depends(get_current_user)):
    return Response(template_bytes(), media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', headers={'Content-Disposition':'attachment; filename=stokonomi_pilot_sablon.xlsx'})

@router.post('/pilot/upload')
async def upload_pilot(file: UploadFile = File(...), db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        dataset, retry = CanonicalExcelIngestionService().stage(db, current_user.company_id, current_user.id, file.filename or '', await file.read())
        validation = dataset.validations[-1]
        return {'dataset_id':str(dataset.id),'status':dataset.state.value,'same_file_retry':retry,'issues':validation.errors or [],'warnings':validation.warnings or [],'summary':{'record_count':dataset.record_count,'material_count':dataset.sku_count},'READY_FOR_ACCEPTANCE':bool(validation.is_valid)}
    except CanonicalExcelError as exc: raise HTTPException(status_code=400, detail=str(exc))

@router.post('/pilot/{dataset_id}/accept')
def accept_pilot(dataset_id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try: return CanonicalExcelIngestionService().accept(db, current_user.company_id, current_user.id, dataset_id)
    except CanonicalExcelError as exc: raise HTTPException(status_code=400 if str(exc) != 'DATASET_UNAVAILABLE' else 404, detail=str(exc))
