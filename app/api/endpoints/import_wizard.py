# app/api/endpoints/import_wizard.py - DÜZELTİLMİŞ

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import tempfile
import os
import shutil

from app.database import get_db
from app.models import User, ValidationResult
from app.auth import get_current_user
from app.services.validation_engine import get_validation_engine
from app.services.normalization_engine import get_normalization_engine
from app.utils.excel_reader import ExcelReader

router = APIRouter()
excel_reader = ExcelReader()

# Geçici sonuç cache'i
validation_cache = {}


@router.post("/import-wizard/validate")
async def validate_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Excel dosyasını doğrula - Tüm adımları çalıştırır
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir (.xlsx, .xls)")
    
    # ✅ Geçici dosya oluştur
    temp_path = None
    try:       

        # Geçici dosyaya kaydet
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name
        
        # ✅ Excel'i oku (read_file kullan)
        read_result = excel_reader.read_file(temp_path)
        
        if not read_result['success']:
            raise HTTPException(
                status_code=400, 
                detail=read_result.get('error', 'Dosya okunamadı')
            )
        
        sheets = read_result['data']
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya okuma hatası: {str(e)}")
    finally:
        # Geçici dosyayı temizle
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
    
    print("🔍 Debug: ExcelReader'dan gelen veri:")
    print(f"📊 Debug: Sheets: {list(sheets.keys())}")
    for sheet_name, data in sheets.items():
        print(f"📄 {sheet_name}: type={type(data)}")
        if isinstance(data, dict):
            print(f"   keys: {list(data.keys())}")
            if 'data' in data and isinstance(data['data'], list) and data['data']:
                print(f"   ilk satır: {data['data'][0]}")
        elif isinstance(data, list) and data:
            print(f"   ilk satır: {data[0]}")

    # Benzersiz upload_id oluştur
    upload_id = str(uuid.uuid4())
    
    # Validation Engine
    engine = get_validation_engine(db, current_user.id, upload_id)
    
    # STEP 1: Dosya Bilgileri
    file_info = engine.get_file_info(
        file_name=file.filename,
        file_size=len(content) if 'content' in dir() else 0,
        sheets=sheets
    )
    
    # STEP 2: Sheet Kontrolü
    sheet_check = engine.check_sheets(sheets)
    
    # STEP 3: Veri Kalitesi
    data_quality = engine.validate_data_quality(sheets)
    
    # STEP 4: Normalizasyon
    normalization = engine.normalize_data(sheets)
    
    # STEP 5: Impact Assessment
    impact = engine.analyze_impact(sheets)
    
    # STEP 6: Özet
    summary = engine.get_summary({
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization,
        'impact': impact
    })
    
    # Sonucu cache'e kaydet
    result_data = {
        'upload_id': upload_id,
        'file_name': file.filename,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization,
        'impact': impact,
        'summary': summary,
        'status': 'validated'
    }
    
    validation_cache[upload_id] = result_data
    
    # Veritabanına kaydet
    validation_result = ValidationResult(
        user_id=current_user.id,
        upload_id=upload_id,
        step=6,
        result_data=result_data,
        status='completed',
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(validation_result)
    db.commit()
    
    return {
        'success': True,
        'upload_id': upload_id,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization,
        'impact': impact,
        'summary': summary
    }


@router.get("/import-wizard/result/{upload_id}")
async def get_validation_result(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validation sonucunu getir"""
    # Önce cache'den dene
    if upload_id in validation_cache:
        return validation_cache[upload_id]
    
    # Cache'de yoksa DB'den al
    result = db.query(ValidationResult).filter(
        ValidationResult.upload_id == upload_id,
        ValidationResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Sonuç bulunamadı")
    
    return result.result_data


@router.post("/import-wizard/apply-normalization")
async def apply_normalization(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Normalizasyon sonuçlarını uygula ve Dataset oluştur"""
    # Cache'den al
    if upload_id not in validation_cache:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı")
    
    result_data = validation_cache[upload_id]
    normalized_data = result_data.get('normalization', {}).get('normalized_data', {})
    
    # Dataset Builder ile Dataset oluştur
    from app.services.dataset_builder import DatasetBuilder
    
    builder = DatasetBuilder(db)
    
    # Temel_Veriler'den materials listesini çıkar
    materials = []
    if 'Temel_Veriler' in normalized_data:
        materials = normalized_data['Temel_Veriler']
    
    # Tedarikçiler
    suppliers = {}
    if 'Tedarikciler' in normalized_data:
        for row in normalized_data['Tedarikciler']:
            code = row.get('Tedarikçi Kodu')
            if code:
                suppliers[code] = row
    
    # Tedarikçi eşleştirme
    supplier_mapping = {}
    if 'Malzeme_Tedarikciler' in normalized_data:
        for row in normalized_data['Malzeme_Tedarikciler']:
            material_code = row.get('Ürün Kodu')
            supplier_code = row.get('Tedarikçi Kodu')
            if material_code and supplier_code:
                if material_code not in supplier_mapping:
                    supplier_mapping[material_code] = []
                supplier_mapping[material_code].append({
                    'supplier_id': supplier_code,
                    'share': row.get('Tedarik Payı (%)', 1.0) / 100
                })
    
    dataset = builder.build_from_materials(
        user_id=current_user.id,
        materials=materials,
        suppliers=suppliers,
        supplier_mapping=supplier_mapping,
        upload_id=upload_id,
        source_type="excel",
        source_name=result_data.get('file_name', 'unknown.xlsx')
    )
    
    # Cache'i temizle
    del validation_cache[upload_id]
    
    return {
        'success': True,
        'dataset_id': dataset.id,
        'message': 'Dataset başarıyla oluşturuldu'
    }

