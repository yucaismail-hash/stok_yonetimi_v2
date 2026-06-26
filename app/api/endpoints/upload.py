from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import User, UploadedData, AnalysisResult
from app.auth import get_current_user, get_current_user_optional  # ✅ Yeni fonksiyon
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
    """Kullanıcının yüklediği verileri getir"""
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

@router.post("/upload")
async def upload_excel(
    file: UploadFile = File(...),
    mode: str = Query("quick", description="Analiz modu: quick veya detailed"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Excel dosyası yükle - SADECE VERİYİ KAYDET, ANALİZ YAPMA!
    Token maliyeti: 0 (ücretsiz)
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
        
        # 4. Verileri cache'e kaydet
        materials = read_result['data']['materials']
        
        # ============================================================
        # 📌 DEBUG: Okunan verileri kontrol et
        # ============================================================
        print(f"\n{'='*60}")
        print("📊 UPLOAD SONRASI VERİ KONTROLÜ")
        print(f"📊 Toplam malzeme: {len(materials)}")
        
        if materials:
            # İlk 3 malzemenin verilerini göster
            for i, m in enumerate(materials[:3]):
                historical = m.get('historical_demand', [])
                print(f"\n📊 Malzeme {i+1}: {m.get('code', '')}")
                print(f"   - Grup: {m.get('group', '')}")
                print(f"   - Lead Time: {m.get('lead_time_days', 0)}")
                print(f"   - EOQ: {m.get('eoq', 0)}")
                print(f"   - Historical Demand uzunluğu: {len(historical)}")
                print(f"   - İlk 5 değer: {historical[:5] if historical else 'BOŞ'}")
                print(f"   - Son 5 değer: {historical[-5:] if historical else 'BOŞ'}")
                print(f"   - Sıfır olmayan: {len([d for d in historical if d != 0])}")
            
            # Tüm malzemelerin veri uzunluklarını göster
            print(f"\n📊 Tüm malzemelerin veri uzunlukları:")
            for m in materials:
                historical = m.get('historical_demand', [])
                print(f"   {m.get('code', '')}: {len(historical)} hafta")
        else:
            print("❌ Hiç malzeme yok!")
        
        print(f"{'='*60}\n")
        # ============================================================
        
        cached_data = {
            'materials': materials,
            'supplier_mapping': read_result['data'].get('supplier_mapping', {}),
            'suppliers': read_result['data'].get('suppliers', {}),
            'week_columns': read_result['data']['week_columns'],
            'file_name': file.filename,
            'uploaded_at': datetime.now().isoformat(),
            'total_materials': len(materials),
            'mode': mode
        }
        
        # ✅ KULLANICI ID'SİNİ DOĞRU AL!
        if current_user:
            user_id = current_user.id
            print(f"🔑 Kullanıcı ID: {user_id} için cache'e kaydediliyor...")
            set_user_upload_data(user_id, cached_data)
            print(f"✅ Cache'e kaydedildi: Kullanıcı {user_id}, {len(materials)} malzeme")
            
            # Veritabanına da kaydet
            user_upload = UploadedData(
                user_id=current_user.id,
                filename=file.filename,
                file_size=0,
                processed_data=cached_data,
                raw_data={"filename": file.filename, "mode": mode},
                status="completed",
                processed_at=datetime.utcnow()
            )
            db.add(user_upload)
            db.commit()
            db.refresh(user_upload)
        else:
            # Token yoksa - bu durumda cache'e kaydetme, sadece hata döndür
            print("❌ Token olmadan upload yapılamaz!")
            return JSONResponse(
                status_code=401,
                content={
                    'success': False,
                    'error': "Lütfen giriş yaparak tekrar deneyin."
                }
            )
        
        return {
            'success': True,
            'message': f"{len(materials)} malzeme başarıyla yüklendi. Analiz için ilgili sayfaya gidin.",
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
            content={
                'success': False,
                'error': f"Sunucu hatası: {str(e)}"
            }
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
    
    # ✅ Cache'de varsa direkt döndür
    if cached_data and cached_data.get('materials'):
        print(f"✅ Cache'den veri bulundu: {len(cached_data.get('materials', []))} malzeme")
        return {
            "has_data": True,
            "filename": cached_data.get('file_name', 'unknown.xlsx'),
            "uploaded_at": cached_data.get('uploaded_at'),
            "status": "completed",
            "materials_count": len(cached_data.get('materials', []))
        }
    
    # ❌ Cache'de yoksa veritabanına gitme, direkt false döndür
    print(f"❌ Cache'de veri yok: Kullanıcı {user_id}")
    return {"has_data": False}

@router.delete("/upload/clear")
def clear_upload_data(
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının yüklediği verileri temizle"""
    if current_user.id in upload_cache:
        del upload_cache[current_user.id]
    return {'success': True, 'message': 'Veriler temizlendi'}

@router.get("/upload/results")
async def get_upload_results(
    result_type: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcının tüm analiz sonuçlarını getir - DÜZELTİLMİŞ"""
    from app.models import UserAnalysisResult, AnalysisResult
    from datetime import datetime
    
    # Benzersiz sonuçları toplamak için set
    seen = set()
    results = []
    
    # 1. UserAnalysisResult'tan normal sonuçları al
    query = db.query(UserAnalysisResult).filter(
        UserAnalysisResult.user_id == current_user.id,
        UserAnalysisResult.expires_at > datetime.utcnow()
    )
    
    if result_type:
        query = query.filter(UserAnalysisResult.result_type == result_type)
    
    user_results = query.order_by(UserAnalysisResult.created_at.desc()).limit(limit).all()
    
    for r in user_results:
        data = r.result_data if isinstance(r.result_data, dict) else {}
        
        # Batch sonucu (içinde results listesi var)
        if 'results' in data and isinstance(data['results'], list):
            for item in data['results']:
                # ✅ Benzersiz anahtar oluştur (material_code + created_at)
                key = f"{item.get('material_code', '')}_{r.created_at.isoformat()}"
                if key not in seen:
                    seen.add(key)
                    results.append({
                        'id': r.id,
                        'created_at': r.created_at,
                        'data': item,
                        'material_code': item.get('material_code', ''),
                        'material_group': item.get('group', ''),
                        'result_type': r.result_type
                    })
        else:
            # Tekil sonuç
            key = f"{r.material_code}_{r.created_at.isoformat()}"
            if key not in seen:
                seen.add(key)
                results.append({
                    'id': r.id,
                    'created_at': r.created_at,
                    'data': data,
                    'material_code': r.material_code,
                    'material_group': r.material_group,
                    'result_type': r.result_type
                })
    
    # 2. AnalysisResult'tan ASYNC tamamlanan sonuçları al
    async_results = db.query(AnalysisResult).filter(
        AnalysisResult.user_id == current_user.id,
        AnalysisResult.result_type == 'forecast_batch_async'
    ).order_by(AnalysisResult.created_at.desc()).limit(limit).all()
    
    for r in async_results:
        data = r.data if isinstance(r.data, dict) else {}
        
        # ✅ Sadece tamamlananları al
        if data.get('status') == 'completed':
            items = data.get('results', [])
            for item in items:
                key = f"{item.get('material_code', '')}_{r.created_at.isoformat()}"
                if key not in seen:
                    seen.add(key)
                    results.append({
                        'id': r.id,
                        'created_at': r.created_at,
                        'data': item,
                        'material_code': item.get('material_code', ''),
                        'material_group': item.get('group', ''),
                        'result_type': 'forecast_batch_async'
                    })
    
    # ✅ Tarihe göre sırala (en yeni önce)
    results.sort(key=lambda x: x['created_at'], reverse=True)
    
    print(f"📊 Toplam {len(results)} benzersiz sonuç bulundu")
    
    return {
        "success": True,
        "total": len(results),
        "results": results
    }

