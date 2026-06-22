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
import tempfile

router = APIRouter()
excel_processor = ExcelProcessor()

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    mode: str = "detailed"  # "quick" veya "detailed"
):
    """
    Excel dosyası yükle, işle, öğren ve sonuçları kaydet.
    mode: 'quick' (hızlı, 100 simülasyon, 13 hafta) veya 'detailed' (detaylı, 500 simülasyon, 26 hafta)
    """
    temp_path = None
    try:
        # 1. Dosya tipi kontrolü
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir (.xlsx, .xls)")
        
        # 2. Dosyayı geçici olarak kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        # 3. Excel işleme motorunu çalıştır
        result = excel_processor.process_excel(temp_path, current_user.id, mode=mode)
        
        # 4. Hataları kontrol et
        if not result['success']:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': result.get('error', 'İşlem başarısız'),
                    'warnings': result.get('warnings', [])
                }
            )
        
        # 5. Başarılı yanıt
        return {
            'success': True,
            'message': f"{result['total_materials']} malzeme başarıyla işlendi",
            'total_materials': result['total_materials'],
            'learning_updated': result['learning_updated'],
            'mode': mode,
            'warnings': result.get('warnings', []),
            'errors': result.get('errors', []),
            'results': result['results'][:10]  # İlk 10 sonucu göster
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                'success': False,
                'error': f"Sunucu hatası: {str(e)}"
            }
        )
    finally:
        # Geçici dosyayı temizle
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


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


@router.post("/upload/validate")
async def validate_excel(
    file: UploadFile = File(...)
):
    """
    Sadece Excel dosyasını doğrula (işleme yapma)
    """
    temp_path = None
    try:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        reader = ExcelProcessor().reader
        result = reader.read_file(temp_path)
        
        return {
            'success': result['success'],
            'errors': result.get('errors', []),
            'warnings': result.get('warnings', []),
            'summary': result.get('summary', {})
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': str(e)}
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass