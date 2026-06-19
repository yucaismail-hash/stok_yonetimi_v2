from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.utils.excel_processor import ExcelProcessor
import shutil
import os
from datetime import datetime

router = APIRouter()
excel_processor = ExcelProcessor()

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Excel dosyası yükle, işle, öğren ve sonuçları kaydet
    """
    try:
        # Dosya tipi kontrolü
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir")
        
        # Dosyayı geçici olarak kaydet
        temp_path = f"temp_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Excel'i işle
        result = excel_processor.process_excel(temp_path, current_user.id)
        
        # Geçici dosyayı temizle
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        if not result['success']:
            return JSONResponse(
                status_code=400,
                content={'success': False, 'error': result.get('error', 'İşlem başarısız')}
            )
        
        return {
            'success': True,
            'message': f"{result['total_materials']} malzeme başarıyla işlendi",
            'total_materials': result['total_materials'],
            'learning_updated': result['learning_updated'],
            'results': result['results'][:5]  # Sadece ilk 5 sonucu göster
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )


@router.get("/upload/results")
def get_upload_results(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    material_code: str = None
):
    """
    Kullanıcının kayıtlı analiz sonuçlarını getir
    """
    results = excel_processor.get_user_results(current_user.id, material_code)
    return {
        'success': True,
        'total': len(results),
        'results': results
    }