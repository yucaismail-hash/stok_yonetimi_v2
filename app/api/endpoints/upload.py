from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import get_current_user
from app.utils.excel_reader import ExcelReader
import shutil
import os
from datetime import datetime
import tempfile
import json

router = APIRouter()
excel_reader = ExcelReader()

# ✅ Geçici veri cache'i (kullanıcı bazlı)
upload_cache = {}

def get_user_upload_data(user_id: int):
    """Kullanıcının yüklediği verileri getir"""
    data = upload_cache.get(user_id)
    if data:
        print(f"✅ Cache verisi bulundu: {data.get('total_materials', 0)} malzeme")
        print(f"✅ materials tipi: {type(data.get('materials', []))}")
        if data.get('materials'):
            print(f"✅ İlk malzeme: {data['materials'][0].keys()}")
    else:
        print(f"❌ Cache verisi yok: {user_id}")
    return data

def set_user_upload_data(user_id: int, data: dict):
    """Kullanıcının yüklediği verileri cache'e kaydet"""
    upload_cache[user_id] = data


@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Excel dosyası yükle - SADECE VERİYİ KAYDET, ANALİZ YAPMA!
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
        
        # 3. Excel'i oku (SADECE OKU, ANALİZ YAPMA!)
        read_result = excel_reader.read_file(temp_path)
        
        if not read_result['success']:
            return JSONResponse(
                status_code=400,
                content={
                    'success': False,
                    'error': read_result['errors'][0] if read_result['errors'] else 'Dosya okunamadı',
                    'warnings': read_result.get('warnings', [])
                }
            )
        
        # 4. Verileri cache'e kaydet (analiz yapmadan)
        materials = read_result['data']['materials']
        
        # Malzeme verilerini sadece gerekli alanlarla kaydet
        cached_data = {
            'materials': materials,
            'supplier_mapping': read_result['data'].get('supplier_mapping', {}),
            'suppliers': read_result['data'].get('suppliers', {}),
            'week_columns': read_result['data']['week_columns'],
            'file_name': file.filename,
            'uploaded_at': datetime.now().isoformat(),
            'total_materials': len(materials)
        }
        
        # ✅ SADECE CACHE'E KAYDET
        set_user_upload_data(current_user.id, cached_data)
        
        return {
            'success': True,
            'message': f"{len(materials)} malzeme başarıyla yüklendi. Analiz için ilgili sayfaya gidin.",
            'total_materials': len(materials),
            'file_name': file.filename,
            'warnings': read_result.get('warnings', [])
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


@router.get("/upload/status")
def get_upload_status(
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının yüklediği veri var mı kontrol et"""
    data = get_user_upload_data(current_user.id)
    return {
        'has_data': data is not None,
        'total_materials': data.get('total_materials', 0) if data else 0,
        'file_name': data.get('file_name') if data else None,
        'uploaded_at': data.get('uploaded_at') if data else None
    }


@router.get("/upload/data")
def get_upload_data(
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının yüklediği verileri getir (analiz için)"""
    data = get_user_upload_data(current_user.id)
    if not data:
        raise HTTPException(status_code=404, detail="Henüz Excel dosyası yüklenmemiş")
    
    return {
        'success': True,
        'data': data
    }


@router.delete("/upload/clear")
def clear_upload_data(
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının yüklediği verileri temizle"""
    if current_user.id in upload_cache:
        del upload_cache[current_user.id]
    return {'success': True, 'message': 'Veriler temizlendi'}

@router.get("/upload/results")
def get_upload_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    result_type: str = None  # ✅ result_type parametresi eklendi
):
    """
    Kullanıcının kayıtlı analiz sonuçlarını getir
    """
    from app.models import UserAnalysisResult
    
    query = db.query(UserAnalysisResult).filter(
        UserAnalysisResult.user_id == current_user.id,
        UserAnalysisResult.expires_at > datetime.utcnow()
    )
    
    # ✅ result_type filtresi eklendi
    if result_type:
        query = query.filter(UserAnalysisResult.result_type == result_type)
    
    results = query.order_by(UserAnalysisResult.created_at.desc()).all()
    
    return {
        'success': True,
        'total': len(results),
        'results': [
            {
                'id': r.id,
                'material_code': r.material_code,
                'data': r.result_data,
                'created_at': r.created_at.isoformat() if r.created_at else None
            }
            for r in results
        ]
    }