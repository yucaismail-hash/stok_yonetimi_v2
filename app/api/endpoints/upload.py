from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import uuid  # ✅ YENİ EKLENDİ
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult, AnalysisInput  # ✅ AnalysisInput EKLENDİ
from app.auth import get_current_user, get_current_user_optional
from app.utils.excel_reader import ExcelReader
from app.utils.excel_processor import ExcelProcessor
import shutil
import os
from datetime import datetime
import tempfile

router = APIRouter()
excel_reader = ExcelReader()
excel_processor = ExcelProcessor()

# ✅ Geçici veri cache'i (kullanıcı bazlı)
upload_cache = {}

def get_user_upload_data(user_id: int):
    """Kullanıcının yüklediği verileri getir - SADECE CACHE!"""
    data = upload_cache.get(user_id)
    if data:
        print(f"✅ Cache verisi bulundu: {data.get('total_materials', 0)} malzeme")
        if data.get('materials'):
            print(f"✅ İlk malzeme: {data['materials'][0].keys() if data['materials'] else 'None'}")
    else:
        print(f"❌ Cache verisi yok: {user_id}")
    return data

def set_user_upload_data(user_id: int, data: dict):
    """Kullanıcının yüklediği verileri cache'e kaydet"""
    upload_cache[user_id] = data

def get_active_upload_id(user_id: int) -> Optional[str]:
    """Kullanıcının aktif upload_id'sini cache'den getir"""
    data = get_user_upload_data(user_id)
    if data:
        return data.get('upload_id')
    return None

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    mode: str = Query("quick", description="Analiz modu: quick veya detailed"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Excel dosyası yükle - Veriyi hem cache'e hem DB'ye kaydet
    Token maliyeti: 0 (ücretsiz)
    """
    temp_path = None
    try:
        # 1. Dosya tipi kontrolü
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir (.xlsx, .xls)")
        
        if not current_user:
            return JSONResponse(
                status_code=401,
                content={'success': False, 'error': "Lütfen giriş yaparak tekrar deneyin."}
            )
        
        # 2. Dosyayı geçici olarak kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            shutil.copyfileobj(file.file, tmp)
            temp_path = tmp.name
        
        # 3. Excel'i oku
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
        
        # 4. Verileri hazırla
        materials = read_result['data']['materials']
        
        # 5. Benzersiz upload_id oluştur
        upload_id = str(uuid.uuid4())
        
        # 6. Cache verisini hazırla
        cached_data = {
            'upload_id': upload_id,  # ✅ YENİ
            'materials': materials,
            'supplier_mapping': read_result['data'].get('supplier_mapping', {}),
            'suppliers': read_result['data'].get('suppliers', {}),
            'week_columns': read_result['data']['week_columns'],
            'file_name': file.filename,
            'uploaded_at': datetime.now().isoformat(),
            'total_materials': len(materials),
            'mode': mode
        }
        
        # 7. Cache'e kaydet
        user_id = current_user.id
        set_user_upload_data(user_id, cached_data)
        print(f"✅ Cache'e kaydedildi: Kullanıcı {user_id}, {len(materials)} malzeme, upload_id: {upload_id}")
        
        # 8. Veritabanına kaydet (AnalysisInput - KALICI)
        analysis_input = AnalysisInput(
            upload_id=upload_id,
            user_id=user_id,
            file_name=file.filename,
            file_size=0,
            data=cached_data,  # Tüm veriyi JSON olarak kaydet
            is_active=True
        )
        db.add(analysis_input)
        
        # 9. UploadedData tablosuna da kaydet (eski sistem uyumu)
        user_upload = UploadedData(
            user_id=user_id,
            filename=file.filename,
            file_size=0,
            processed_data=cached_data,
            raw_data={"filename": file.filename, "mode": mode, "upload_id": upload_id},
            status="completed",
            processed_at=datetime.utcnow()
        )
        db.add(user_upload)
        db.commit()
        
        print(f"✅ Veritabanına kaydedildi: upload_id: {upload_id}")
        
        return {
            'success': True,
            'message': f"{len(materials)} malzeme başarıyla yüklendi.",
            'upload_id': upload_id,  # ✅ DÖNDÜR
            'total_materials': len(materials),
            'file_name': file.filename,
            'mode': mode,
            'warnings': read_result.get('warnings', [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Upload hatası: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={'success': False, 'error': f"Sunucu hatası: {str(e)}"}
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

@router.get("/upload/status")
async def get_upload_status(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Kullanıcının yükleme durumunu kontrol et - SADECE CACHE!
    Token maliyeti: 0 (ücretsiz)
    """
    if not current_user:
        return {"has_data": False, "message": "Giriş yapılmamış"}
    
    user_id = current_user.id
    cached_data = get_user_upload_data(user_id)
    
    if cached_data and cached_data.get('materials'):
        materials = cached_data.get('materials', [])
        
        # ✅ Hafta sayısını hesapla
        week_count = 0
        if materials:
            # İlk malzemenin historical_demand uzunluğu
            first_material = materials[0] if materials else {}
            historical = first_material.get('historical_demand', [])
            week_count = len(historical)
        
        return {
            "has_data": True,
            "upload_id": cached_data.get('upload_id'),
            "filename": cached_data.get('file_name', 'unknown.xlsx'),
            "uploaded_at": cached_data.get('uploaded_at'),
            "status": "completed",
            "materials_count": len(materials),
            "week_count": week_count,  # ✅ EKLENDİ
        }
    
    return {"has_data": False}

@router.get("/upload/materials-info")
async def get_materials_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Yüklenen verilerin detaylı bilgisini getir.
    """
    cached_data = get_user_upload_data(current_user.id)
    if not cached_data:
        return {"has_data": False, "message": "Veri bulunamadı"}
    
    materials = cached_data.get('materials', [])
    
    # ✅ Hafta sayısını hesapla
    week_count = 0
    if materials:
        first_material = materials[0] if materials else {}
        historical = first_material.get('historical_demand', [])
        week_count = len(historical)
    
    return {
        "has_data": True,
        "materials_count": len(materials),
        "week_count": week_count,
        "total_materials": len(materials),
        "file_name": cached_data.get('file_name')
    }

@router.delete("/upload/clear")
def clear_upload_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kullanıcının yüklediği verileri temizle (Cache + DB)"""
    user_id = current_user.id
    
    # 1. Cache'den temizle
    if user_id in upload_cache:
        del upload_cache[user_id]
    
    # 2. Veritabanından pasif yap (silme, is_active=False)
    db.query(AnalysisInput).filter(
        AnalysisInput.user_id == user_id,
        AnalysisInput.is_active == True
    ).update({"is_active": False})
    db.commit()
    
    return {'success': True, 'message': 'Veriler temizlendi'}

# app/api/endpoints/upload.py

# app/api/endpoints/upload.py - SADECE get_upload_results fonksiyonu


@router.get("/upload/results")
async def get_upload_results(
    result_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Kullanıcının tüm analiz sonuçlarını getir.
    SADECE analysis_results tablosundan okur.
    """
    from app.models import AnalysisResult
    from datetime import datetime
    
    results = []
    seen = set()
    
    # ============================================================
    # 📌 TEK TABLO: analysis_results
    # ============================================================
    
    query = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id
    )
    
    if result_type:
        query = query.filter(AnalysisResult.result_type.like(f"{result_type}%"))
    
    # ✅ Sadece tamamlanmış veya senkron olanları al
    query = query.filter(
        (AnalysisResult.status == None) | (AnalysisResult.status == 'completed')
    )
    
    db_results = query.order_by(AnalysisResult.created_at.desc()).limit(limit).all()
    
    print(f"📊 analysis_results: {len(db_results)} kayıt (filtre: {result_type}%)")
    
    for r in db_results:
        data = r.data if isinstance(r.data, dict) else {}
        items = data.get('results', [])
        is_async = r.task_id is not None
        
        # ✅ SADECE BATCH KAYDI EKLE (malzemeleri TEK TEK EKLEME!)
        key = f"result_{r.id}_{r.created_at.isoformat()}"
        if key not in seen:
            seen.add(key)
            results.append({
                'id': r.id,
                'created_at': r.created_at,
                'result_type': r.result_type,
                'material_code': 'BATCH',
                'material_group': 'TOPLU',
                'source': 'analysis_results',
                'is_batch': True,
                'is_async': is_async,
                'is_completed': True,
                'task_id': r.task_id,
                'status': r.status or 'completed',
                'progress': r.progress or 100,
                'total_materials': r.total_materials or len(items),
                'data': data
            })
    
    results.sort(key=lambda x: x['created_at'], reverse=True)
    
    print(f"📊 Toplam {len(results)} benzersiz sonuç bulundu (filtre: {result_type}%)")
    
    return {
        "success": True,
        "total": len(results),
        "results": results
    }

