# app/api/endpoints/import_wizard.py - GÜNCELLENDİ

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import tempfile
import os

from app.database import get_db
from app.models import User, ValidationResult
from app.auth import get_current_user
from app.services.validation_engine import get_validation_engine
from app.services.normalization_engine import get_normalization_engine
from app.services.dataset_builder import DatasetBuilder
from app.utils.excel_reader import ExcelReader
from app.schemas.canonical import (
    CANONICAL_MAP, 
    FIELD_TYPES, 
    SHEET_FIELDS, 
    CRITICAL_FIELDS,
    OPTIONAL_FIELDS,  # ✅ EKLENDI
    get_canonical_field, 
    get_excel_column
)

router = APIRouter()
excel_reader = ExcelReader()

# ============================================================
# ✅ CACHE YAPISI
# ============================================================
validation_cache = {}

def get_cache(upload_id: str) -> Optional[Dict[str, Any]]:
    """Cache'den validation sonucunu alır."""
    return validation_cache.get(upload_id)

def set_cache(upload_id: str, data: Dict[str, Any]) -> None:
    """Validation sonucunu cache'e kaydeder."""
    validation_cache[upload_id] = data

def delete_cache(upload_id: str) -> None:
    """Cache'den validation sonucunu siler."""
    if upload_id in validation_cache:
        del validation_cache[upload_id]


# app/api/endpoints/import_wizard.py - validate_excel TAM KOD

@router.post("/import-wizard/validate")
async def validate_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Excel dosyasını doğrula - Validation + Normalization yapar.
    
    Akış:
    1. Dosyayı oku
    2. Sheet kontrolü (structural)
    3. Veri kalitesi kontrolü (validation)
    4. Normalization (standardizasyon)
    5. Impact analizi
    6. Cache'e kaydet
    7. Sonuçları döndür
    """
    # ============================================================
    # 1. Dosya tipi kontrolü
    # ============================================================
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Sadece Excel dosyaları kabul edilir (.xlsx, .xls)")

    # ============================================================
    # 2. Dosyayı oku
    # ============================================================
    temp_path = None
    content = None
    sheets = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            temp_path = tmp.name

        read_result = excel_reader.read_file(temp_path)
        if not read_result['success']:
            raise HTTPException(
                status_code=400, 
                detail=read_result.get('error', 'Dosya okunamadı')
            )

        sheets = read_result['data']
        
        # ============================================================
        # DEBUG: sheets içeriğini kontrol et
        # ============================================================
        print(f"🔍 sheets keys: {list(sheets.keys())}")
        
        if 'materials' in sheets:
            materials = sheets['materials']
            if materials and isinstance(materials, list) and len(materials) > 0:
                print(f"🔍 materials ilk 3 satır:")
                for i, mat in enumerate(materials[:3]):
                    if isinstance(mat, dict):
                        print(f"   Satır {i+1}: product_code={mat.get('product_code', 'BULUNAMADI!')}, description={mat.get('description', '')[:30]}")
                    else:
                        print(f"   Satır {i+1}: {type(mat)} - {mat}")
            else:
                print("🔍 materials boş veya liste değil!")
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya okuma hatası: {str(e)}")
    finally:
        # Geçici dosyayı temizle
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass

    # ============================================================
    # 3. Benzersiz upload_id oluştur
    # ============================================================
    upload_id = str(uuid.uuid4())
    
    # ============================================================
    # 4. Validation Engine
    # ============================================================
    validation_engine = get_validation_engine(db, current_user.id, upload_id)
    
    # STEP 1: Dosya Bilgileri
    file_info = validation_engine.get_file_info(
        file_name=file.filename,
        file_size=len(content) if content else 0,
        sheets=sheets
    )
    print(f"🔍 Dosya bilgileri: {file_info['file_name']}, {file_info['total_rows']} satır")
    
    # STEP 2: Sheet Kontrolü (structural)
    sheet_check = validation_engine.check_sheets(sheets)
    print(f"🔍 Sheet kontrolü: {sheet_check.get('summary', '')}")
    
    # STEP 3: Veri Kalitesi (kapsamlı validation)
    data_quality = validation_engine.validate_data_quality(sheets)
    print(f"🔍 Veri kalitesi skoru: %{data_quality.get('summary', {}).get('score', 0):.1f}")
    print(f"🔍 can_proceed: {data_quality.get('can_proceed', True)}")
    
# app/api/endpoints/import_wizard.py - /validate endpoint'i

    # ============================================================
    # 5. Normalization Engine
    # ============================================================
    normalization_engine = get_normalization_engine(db, current_user.id, upload_id)
    normalization_result = normalization_engine.normalize_data(sheets)
    
    # ============================================================
    # ✅ Validation hatalarını normalization sonucuna ekle
    # ============================================================
    
    # Opsiyonel alanları al
    optional_fields = []
    for sheet_name in OPTIONAL_FIELDS:
        optional_fields.extend(OPTIONAL_FIELDS.get(sheet_name, []))
    
    # 1. Data type errors
    data_type_errors = data_quality.get('data_type_errors', [])
    for err in data_type_errors:
        field = err.get('canonical_field')
        if field in optional_fields:
            continue
        normalization_result['errors'].append({
            'sheet': err.get('sheet', ''),
            'row': err.get('row', ''),
            'column': err.get('column', ''),
            'value': err.get('original_value', ''),
            'original_value': err.get('original_value', ''),
            'message': err.get('message', ''),
            'type': 'data_type_error',
            'severity': err.get('severity', 'critical'),
        })
        normalization_result['total_errors'] += 1
    
    # 2. Business rule errors
    business_rule_errors = data_quality.get('business_rule_errors', [])
    for err in business_rule_errors:
        field = err.get('canonical_field')
        if field in optional_fields:
            continue
        normalization_result['errors'].append({
            'sheet': err.get('sheet', ''),
            'row': err.get('row', ''),
            'column': err.get('column', ''),
            'value': err.get('original_value', ''),
            'original_value': err.get('original_value', ''),
            'message': err.get('message', ''),
            'type': 'business_rule_error',
            'severity': err.get('severity', 'critical'),
            'rows': err.get('rows', []),
        })
        normalization_result['total_errors'] += 1
    
    # 3. Structural errors (critical olanlar)
    structural_errors = data_quality.get('structural_errors', [])
    for err in structural_errors:
        if err.get('severity') == 'critical':
            normalization_result['errors'].append({
                'sheet': err.get('sheet', ''),
                'row': None,
                'column': err.get('column', ''),
                'value': None,
                'original_value': None,
                'message': err.get('message', ''),
                'type': 'structural_error',
                'severity': 'critical',
            })
            normalization_result['total_errors'] += 1
    
    print(f"🔍 Normalization sonucu (validation hataları eklendi):")
    print(f"   - Otomatik düzeltme: {normalization_result.get('total_changes', 0)}")
    print(f"   - Öneri: {normalization_result.get('total_suggestions', 0)}")
    print(f"   - Manuel düzeltme: {normalization_result.get('total_errors', 0)}")
    
    # ============================================================
    # 6. Impact Assessment (validation sonuçlarını kullanarak)
    # ============================================================
    impact = validation_engine.analyze_impact(sheets, data_quality)
    print(f"🔍 Impact skoru: %{impact.get('overall_score', 0):.1f}")
    
    # ============================================================
    # 7. Genel can_proceed hesapla
    # ============================================================
    can_proceed = sheet_check.get('can_proceed', True) and data_quality.get('can_proceed', True)
    print(f"🔍 Genel can_proceed: {can_proceed}")
    
    # ============================================================
    # 8. Cache'e kaydet (sheets ve normalization verisi dahil)
    # ============================================================
    result_data = {
        'upload_id': upload_id,
        'file_name': file.filename,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization_result,      # ✅ normalization eklendi
        'impact': impact,
        'can_proceed': can_proceed,
        'sheets': sheets,                           # sheets verisi cache'te
        'normalized_data': normalization_result.get('normalized_data', {}),  # normalize edilmiş veri
        'status': 'validated_and_normalized'
    }
    set_cache(upload_id, result_data)
    
    # ============================================================
    # 9. Veritabanına kaydet
    # ============================================================
    validation_result = ValidationResult(
        user_id=current_user.id,
        upload_id=upload_id,
        step=6,  # Tüm adımlar tamamlandı
        result_data=result_data,
        status='completed',
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    db.add(validation_result)
    db.commit()
    
    # ============================================================
    # 10. Sonuçları döndür (sheets verisi hariç - gereksiz büyük)
    # ============================================================
    return {
        'success': True,
        'upload_id': upload_id,
        'can_proceed': can_proceed,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization_result,  # ✅ normalization döndürülüyor
        'impact': impact,
    }

@router.post("/import-wizard/normalize")
async def normalize_excel(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Normalization yap ve dataset oluşturmak için hazırla (can_proceed kontrolü)."""
    
    cache_data = get_cache(upload_id)
    if not cache_data:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı.")

    can_proceed = cache_data.get('can_proceed', True)
    sheets = cache_data.get('sheets')
    
    if not sheets:
        raise HTTPException(status_code=400, detail="Sheet verisi bulunamadı.")

    if not can_proceed:
        critical_errors = []
        data_quality = cache_data.get('data_quality', {})
        for key in ['structural_errors', 'missing_data', 'data_type_errors', 'business_rule_errors']:
            for err in data_quality.get(key, []):
                if err.get('severity') == 'critical':
                    critical_errors.append(err.get('message', ''))
        error_msg = f"Dataset oluşturulamıyor. Kritik hatalar: {', '.join(critical_errors[:5])}"
        raise HTTPException(status_code=400, detail=error_msg)

    # ============================================================
    # ✅ Normalization yap
    # ============================================================
    engine = get_normalization_engine(db, current_user.id, upload_id)
    normalization_result = engine.normalize_data(sheets)
    
    # ============================================================
    # ✅ Validation'dan gelen hataları normalization_result'a ekle
    # ============================================================
    data_quality = cache_data.get('data_quality', {})
    
    # app/api/endpoints/import_wizard.py - /validate endpoint'i

    # ============================================================
    # Validation hatalarını normalization sonucuna ekle (sadece critical olanlar)
    # ============================================================
    optional_fields = OPTIONAL_FIELDS.get('Temel_Veriler', [])
    
    # Data type errors - sadece opsiyonel olmayanlar
    data_type_errors = data_quality.get('data_type_errors', [])
    for err in data_type_errors:
        field = err.get('canonical_field')
        # ✅ Opsiyonel alanları atla
        if field in optional_fields:
            continue
        normalization_result['errors'].append({
            'sheet': err.get('sheet', ''),
            'row': err.get('row', ''),
            'column': err.get('column', ''),
            'value': err.get('original_value', ''),
            'original_value': err.get('original_value', ''),
            'message': err.get('message', ''),
            'type': 'data_type_error',
            'severity': err.get('severity', 'critical'),
        })
        normalization_result['total_errors'] += 1
    
    # Business rule errors - sadece opsiyonel olmayanlar
    business_rule_errors = data_quality.get('business_rule_errors', [])
    for err in business_rule_errors:
        field = err.get('canonical_field')
        # ✅ Opsiyonel alanları atla
        if field in optional_fields:
            continue
        normalization_result['errors'].append({
            'sheet': err.get('sheet', ''),
            'row': err.get('row', ''),
            'column': err.get('column', ''),
            'value': err.get('original_value', ''),
            'original_value': err.get('original_value', ''),
            'message': err.get('message', ''),
            'type': 'business_rule_error',
            'severity': err.get('severity', 'critical'),
            'rows': err.get('rows', []),
        })
        normalization_result['total_errors'] += 1
    
    # ============================================================
    # ✅ Cache'i güncelle
    # ============================================================
    cache_data['normalization'] = normalization_result
    cache_data['normalized_data'] = normalization_result.get('normalized_data', {})
    cache_data['status'] = 'normalized'
    set_cache(upload_id, cache_data)

    return {
        'success': True,
        'upload_id': upload_id,
        'total_changes': normalization_result.get('total_changes', 0),
        'total_suggestions': normalization_result.get('total_suggestions', 0),
        'total_errors': normalization_result.get('total_errors', 0),
        'normalization': normalization_result
    }

@router.post("/import-wizard/apply-dataset")
async def apply_dataset(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dataset oluştur (normalization uygulanmış veriden). Önce can_proceed kontrolü."""
    
    # Cache'den veriyi al
    cache_data = get_cache(upload_id)
    if not cache_data:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı. Lütfen dosyayı yeniden yükleyin.")

    can_proceed = cache_data.get('can_proceed', True)
    normalized_data = cache_data.get('normalized_data')
    
    if not normalized_data:
        raise HTTPException(status_code=400, detail="Normalization yapılmamış. Lütfen önce normalizasyonu tamamlayın.")

    # DATASET GATE: can_proceed kontrol et
    if not can_proceed:
        critical_errors = []
        data_quality = cache_data.get('data_quality', {})
        for key in ['structural_errors', 'missing_data', 'data_type_errors', 'business_rule_errors']:
            for err in data_quality.get(key, []):
                if err.get('severity') == 'critical':
                    critical_errors.append(err.get('message', ''))
        error_msg = f"Dataset oluşturulamıyor. Kritik hatalar: {', '.join(critical_errors[:5])}"
        raise HTTPException(status_code=400, detail=error_msg)

    # Dataset Builder ile dataset oluştur
    builder = DatasetBuilder(db)
    
    try:
        # normalized_data'dan materials listesini çıkar
        # normalized_data yapısı: {'Temel_Veriler': [...], 'Tedarikciler': {...}, 'Malzeme_Tedarikciler': {...}}
        materials = []
        if 'Temel_Veriler' in normalized_data:
            materials = normalized_data['Temel_Veriler']
        
        # Tedarikçiler
        suppliers = {}
        if 'Tedarikciler' in normalized_data:
            # Tedarikciler dict olarak gelir
            suppliers = normalized_data['Tedarikciler']
        
        # Tedarikçi eşleştirme
        supplier_mapping = {}
        if 'Malzeme_Tedarikciler' in normalized_data:
            for row in normalized_data['Malzeme_Tedarikciler']:
                material_code = row.get('Ürün Kodu') or row.get('product_code')
                supplier_code = row.get('Tedarikçi Kodu') or row.get('supplier_id')
                if material_code and supplier_code:
                    if material_code not in supplier_mapping:
                        supplier_mapping[material_code] = []
                    supplier_mapping[material_code].append({
                        'supplier_id': supplier_code,
                        'share': row.get('Tedarik Payı (%)', 1.0) / 100
                    })
        
        # Dataset oluştur
        dataset = builder.build_from_materials(
            user_id=current_user.id,
            materials=materials,
            suppliers=suppliers,
            supplier_mapping=supplier_mapping,
            upload_id=upload_id,
            source_type="excel",
            source_name=cache_data.get('file_name', 'unknown.xlsx'),
            validation_result=cache_data  # Dataset Gate için
        )
        
        # Cache'i temizle
        delete_cache(upload_id)
        
        return {
            'success': True,
            'dataset_id': dataset.id,
            'message': 'Dataset başarıyla oluşturuldu'
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Dataset oluşturma hatası: {e}")
        raise HTTPException(status_code=500, detail=f"Dataset oluşturulurken hata oluştu: {str(e)}")


@router.post("/import-wizard/re-validate")
async def re_validate(
    upload_id: str,
    corrections: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Kullanıcı düzeltmeleri sonrası yeniden validation yap."""
    
    # Cache'den veriyi al
    cache_data = get_cache(upload_id)
    if not cache_data:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı.")

    sheets = cache_data.get('sheets')
    if not sheets:
        raise HTTPException(status_code=400, detail="Sheet verisi bulunamadı.")

    # ============================================================
    # Kullanıcı düzeltmelerini uygula
    # ============================================================
    # corrections formatı: {'sheetname_row_column': 'new_value'}
    # Örnek: {'Temel_Veriler_1_product_code': 'ABC001'}
    
    for key, new_value in corrections.items():
        # key formatı: sheet_row_column
        parts = key.split('_')
        if len(parts) < 3:
            continue
        
        sheet_name = parts[0]
        try:
            row_idx = int(parts[1]) - 1  # 1-based'den 0-based'e
        except:
            continue
        
        # column adını birleştir (birden fazla _ olabilir)
        column = '_'.join(parts[2:])
        
        # Sheet'i bul
        if sheet_name not in sheets:
            continue
        
        rows = sheets[sheet_name]
        if row_idx >= len(rows):
            continue
        
        # Değeri güncelle
        if isinstance(rows[row_idx], dict):
            rows[row_idx][column] = new_value
    
    # ============================================================
    # Yeniden validation çalıştır
    # ============================================================
    engine = get_validation_engine(db, current_user.id, upload_id)
    
    # Sheet kontrolü
    sheet_check = engine.check_sheets(sheets)
    
    # Veri kalitesi
    data_quality = engine.validate_data_quality(sheets)
    
    # Impact
    impact = engine.analyze_impact(sheets, data_quality)
    
    # can_proceed
    can_proceed = sheet_check.get('can_proceed', True) and data_quality.get('can_proceed', True)
    
    # Cache'i güncelle
    cache_data['sheet_check'] = sheet_check
    cache_data['data_quality'] = data_quality
    cache_data['impact'] = impact
    cache_data['can_proceed'] = can_proceed
    cache_data['sheets'] = sheets
    set_cache(upload_id, cache_data)
    
    # Validation sonucunu veritabanına kaydet
    validation_result = db.query(ValidationResult).filter(
        ValidationResult.upload_id == upload_id,
        ValidationResult.user_id == current_user.id
    ).first()
    
    if validation_result:
        validation_result.result_data = cache_data
        validation_result.updated_at = datetime.utcnow()
        db.commit()
    
    return {
        'success': True,
        'upload_id': upload_id,
        'can_proceed': can_proceed,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'impact': impact,
        'validation_data': cache_data
    }


@router.get("/import-wizard/result/{upload_id}")
async def get_validation_result(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validation sonucunu getir."""
    
    # Önce cache'den dene
    cache_data = get_cache(upload_id)
    if cache_data:
        return cache_data
    
    # Cache'de yoksa DB'den al
    result = db.query(ValidationResult).filter(
        ValidationResult.upload_id == upload_id,
        ValidationResult.user_id == current_user.id
    ).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Sonuç bulunamadı")
    
    return result.result_data


@router.delete("/import-wizard/cache/{upload_id}")
async def clear_cache(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cache'deki validation sonucunu temizler."""
    
    # Cache'den sil
    delete_cache(upload_id)
    
    # DB'den de sil (opsiyonel)
    result = db.query(ValidationResult).filter(
        ValidationResult.upload_id == upload_id,
        ValidationResult.user_id == current_user.id
    ).delete()
    db.commit()
    
    return {
        'success': True,
        'message': 'Cache temizlendi'
    }