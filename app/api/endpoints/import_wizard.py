# app/api/endpoints/import_wizard.py - TAM VE GÜNCEL

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import tempfile
import os
import logging

from app.database import get_db
from app.models import *
from app.auth import get_current_user
from app.services.validation_engine import get_validation_engine
from app.services.normalization_engine import get_normalization_engine
from app.services.dataset_builder import DatasetBuilder
from app.utils.excel_reader import ExcelReader
from app.services.active_dataset import get_active_dataset_service
from app.schemas.canonical import (
    CANONICAL_MAP, 
    FIELD_TYPES, 
    SHEET_FIELDS, 
    CRITICAL_FIELDS,
    OPTIONAL_FIELDS,
    get_canonical_field, 
    get_excel_column
)
from app.schemas.import_wizard import (
    ReValidateRequest,
    NormalizeRequest,
    ApplyDatasetRequest
)

logger = logging.getLogger(__name__)

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


# ============================================================
# 1. VALIDATE EXCEL ENDPOINT
# ============================================================
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
        
        # DEBUG: sheets içeriğini kontrol et
        print(f"🔍 sheets keys: {list(sheets.keys())}")
        
        if 'materials' in sheets:
            materials = sheets['materials']
            if materials and isinstance(materials, list) and len(materials) > 0:
                print(f"🔍 materials ilk 3 satır (ham ExcelReader çıktısı):")
                for i, mat in enumerate(materials[:3]):
                    if isinstance(mat, dict):
                        print(f"   Satır {i+1}:")
                        print(f"      product_code={mat.get('product_code', 'BULUNAMADI!')!r}")
                        print(f"      unit_cost={mat.get('unit_cost', 'BULUNAMADI!')!r}")
                        print(f"      holding_rate={mat.get('holding_rate', 'BULUNAMADI!')!r}")
                        print(f"      shortage_cost={mat.get('shortage_cost', 'BULUNAMADI!')!r}")
                        print(f"      description={mat.get('description', '')[:30]!r}")
                    else:
                        print(f"   Satır {i+1}: {type(mat)} - {mat}")
            else:
                print("🔍 materials boş veya liste değil!")
                
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Dosya okuma hatası: {str(e)}")
    finally:
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
    
    # ============================================================
    # 4b. Validation hatalarını topla (normalization'a aktarmak için)
    # ============================================================
    
    # ✅ OPTIONAL_FIELDS'ı al
    optional_fields = []
    for sheet_name in OPTIONAL_FIELDS:
        optional_fields.extend(OPTIONAL_FIELDS.get(sheet_name, []))
    
    validation_errors = []
    
    # Business rule errors - critical olanlar
    for err in data_quality.get('business_rule_errors', []):
        if err.get('severity') == 'critical' or err.get('requires_user_action'):
            validation_errors.append({
                'sheet': err.get('sheet', ''),
                'row': err.get('row', ''),
                'column': err.get('column', ''),
                'canonical_field': err.get('canonical_field', ''),
                'value': err.get('original_value', ''),
                'original_value': err.get('original_value', ''),
                'message': err.get('message', ''),
                'type': 'business_rule_error',
                'severity': err.get('severity', 'critical'),
                'rows': err.get('rows', []),
                'requires_user_action': True
            })
    
    # Data type errors - opsiyonel alanlarda geçersiz değerler gösterilir!
    for err in data_quality.get('data_type_errors', []):
        field = err.get('canonical_field')
        value = err.get('original_value')
        
        is_optional = field in optional_fields
        
        # Opsiyonel ve değer boşsa atla
        if is_optional and (value is None or str(value).strip() == ''):
            continue
        
        # Geçersiz değer varsa (opsiyonel olsa bile) göster
        validation_errors.append({
            'sheet': err.get('sheet', ''),
            'row': err.get('row', ''),
            'column': err.get('column', ''),
            'canonical_field': err.get('canonical_field', ''),
            'value': err.get('original_value', ''),
            'original_value': err.get('original_value', ''),
            'message': err.get('message', ''),
            'type': 'data_type_error',
            'severity': err.get('severity', 'warning'),
            'requires_user_action': True
        })
    
    # Missing data - critical olanlar (product_code gibi)
    for err in data_quality.get('missing_data', []):
        if err.get('severity') == 'critical':
            missing_rows = err.get('missing_rows_list', [])
            for row_num in missing_rows:
                validation_errors.append({
                    'sheet': err.get('sheet', ''),
                    'row': row_num,
                    'column': err.get('column', ''),
                    'canonical_field': err.get('canonical_field', ''),
                    'value': None,
                    'original_value': None,
                    'message': f"{row_num}. satırda {err.get('column', '')} eksik!",
                    'type': 'missing_data',
                    'severity': 'critical',
                    'requires_user_action': True
                })
    
    # ============================================================
    # 5. Normalization Engine (validation_errors'u gönder)
    # ============================================================
    sheets_with_errors = sheets.copy()
    sheets_with_errors['_validation_errors'] = validation_errors
    
    normalization_engine = get_normalization_engine(db, current_user.id, upload_id)
    normalization_result = normalization_engine.normalize_data(sheets_with_errors)
    
    print(f"🔍 Normalization sonucu (validation hataları eklendi):")
    print(f"   - Otomatik düzeltme: {normalization_result.get('total_changes', 0)}")
    print(f"   - Öneri: {normalization_result.get('total_suggestions', 0)}")
    print(f"   - Manuel düzeltme: {normalization_result.get('total_errors', 0)}")
    
    # ============================================================
    # 6. Impact Assessment
    # ============================================================
    impact = validation_engine.analyze_impact(sheets, data_quality)
    print(f"🔍 Impact skoru: %{impact.get('overall_score', 0):.1f}")
    
    # ============================================================
    # 7. Genel can_proceed hesapla
    # ============================================================
    can_proceed = sheet_check.get('can_proceed', True) and data_quality.get('can_proceed', True)
    print(f"🔍 Genel can_proceed: {can_proceed}")
    
    # ============================================================
    # 8. Cache'e kaydet
    # ============================================================
    result_data = {
        'upload_id': upload_id,
        'file_name': file.filename,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization_result,
        'impact': impact,
        'can_proceed': can_proceed,
        'sheets': sheets,
        'normalized_data': normalization_result.get('normalized_data', {}),
        'status': 'validated_and_normalized'
    }
    set_cache(upload_id, result_data)
    
    # ============================================================
    # 9. Veritabanına kaydet
    # ============================================================
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
    
    # ============================================================
    # 10. Sonuçları döndür
    # ============================================================
    return {
        'success': True,
        'upload_id': upload_id,
        'can_proceed': can_proceed,
        'file_info': file_info,
        'sheet_check': sheet_check,
        'data_quality': data_quality,
        'normalization': normalization_result,
        'impact': impact,
    }


# ============================================================
# 2. NORMALIZE EXCEL ENDPOINT
# ============================================================
@router.post("/import-wizard/normalize")
async def normalize_excel(
    request: NormalizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Normalization yap ve dataset oluşturmak için hazırla (can_proceed kontrolü)."""
    
    upload_id = request.upload_id
    
    cache_data = get_cache(upload_id)
    if not cache_data:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı. Lütfen dosyayı yeniden yükleyin.")

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

    # Normalization yap
    engine = get_normalization_engine(db, current_user.id, upload_id)
    normalization_result = engine.normalize_data(sheets)
    
    # Normalize edilmiş veriyi cache'e ekle
    cache_data['normalization'] = normalization_result
    cache_data['status'] = 'normalized'
    cache_data['normalized_data'] = normalization_result.get('normalized_data', {})
    set_cache(upload_id, cache_data)

    return {
        'success': True,
        'upload_id': upload_id,
        'total_changes': normalization_result.get('total_changes', 0),
        'total_suggestions': normalization_result.get('total_suggestions', 0),
        'total_errors': normalization_result.get('total_errors', 0),
        'normalization': normalization_result
    }


# ============================================================
# 3. APPLY DATASET ENDPOINT
# ============================================================

# app/api/endpoints/import_wizard.py - apply_dataset (TAM DÜZELTİLMİŞ)

@router.post("/import-wizard/apply-dataset")
async def apply_dataset(
    request: ApplyDatasetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dataset oluştur ve aktif yap.
    """
    
    upload_id = request.upload_id
    
    # Cache'den veriyi al
    cache_data = get_cache(upload_id)
    if not cache_data:
        raise HTTPException(status_code=404, detail="Validation sonucu bulunamadı. Lütfen dosyayı yeniden yükleyin.")

    can_proceed = cache_data.get('can_proceed', True)
    normalized_data = cache_data.get('normalized_data')
    
    if not normalized_data:
        raise HTTPException(status_code=400, detail="Normalization yapılmamış. Lütfen önce normalizasyonu tamamlayın.")

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
    # ✅ DEBUG: normalized_data içeriğini kontrol et
    # ============================================================
    print(f"🔍 normalized_data keys: {list(normalized_data.keys())}")
    
    # materials
    materials = normalized_data.get('materials', [])
    if not materials:
        materials = normalized_data.get('Temel_Veriler', [])
    print(f"🔍 materials: type={type(materials)}, len={len(materials)}")
    if materials and isinstance(materials, list):
        print(f"   ilk material keys: {list(materials[0].keys()) if materials else 'empty'}")

    # ============================================================
    # ✅ SUPPLIERS - normalized_data'dan al
    # ============================================================
    suppliers = normalized_data.get('suppliers', {})
    if not suppliers:
        suppliers = normalized_data.get('Tedarikciler', {})
    
    print(f"🔍 suppliers (ham): type={type(suppliers)}, len={len(suppliers) if isinstance(suppliers, (dict, list)) else 'unknown'}")
    
    # ✅ Eğer suppliers bir list ise dict'e çevir (DatasetBuilder dict bekliyor)
    if isinstance(suppliers, list):
        print(f"⚠️ suppliers bir list! {len(suppliers)} satır, dict'e dönüştürülüyor...")
        converted_suppliers = {}
        for idx, item in enumerate(suppliers):
            if isinstance(item, dict):
                # supplier_id'yi bul
                supplier_id = item.get('supplier_id') or item.get('Tedarikçi Kodu') or item.get('code')
                if supplier_id:
                    converted_suppliers[str(supplier_id)] = item
                else:
                    print(f"   ⚠️ {idx}. satırda supplier_id bulunamadı: {item.keys() if isinstance(item, dict) else 'not dict'}")
        suppliers = converted_suppliers
        print(f"   dönüştürüldü: {len(suppliers)} tedarikçi")
    elif not isinstance(suppliers, dict):
        print(f"   ⚠️ suppliers bilinmeyen tip: {type(suppliers)}")
        suppliers = {}
    
    print(f"🔍 suppliers (son): type={type(suppliers)}, len={len(suppliers)}")
    if suppliers and isinstance(suppliers, dict):
        print(f"   suppliers keys: {list(suppliers.keys())}")

    # ============================================================
    # ✅ SUPPLIER_MAPPING - normalized_data'dan al
    # ============================================================
    supplier_mapping = normalized_data.get('supplier_mapping', {})
    if not supplier_mapping:
        supplier_mapping = normalized_data.get('Malzeme_Tedarikciler', {})
    
    print(f"🔍 supplier_mapping (ham): type={type(supplier_mapping)}, len={len(supplier_mapping) if isinstance(supplier_mapping, (dict, list)) else 'unknown'}")
    
    # ✅ Eğer supplier_mapping bir list ise dict'e çevir (DatasetBuilder dict bekliyor)
    if isinstance(supplier_mapping, list):
        print(f"⚠️ supplier_mapping bir list! {len(supplier_mapping)} satır, dict'e dönüştürülüyor...")
        converted_mapping = {}
        for idx, item in enumerate(supplier_mapping):
            if isinstance(item, dict):
                product_code = item.get('product_code') or item.get('Ürün Kodu')
                supplier_id = item.get('supplier_id') or item.get('Tedarikçi Kodu')
                if product_code and supplier_id:
                    if product_code not in converted_mapping:
                        converted_mapping[product_code] = []
                    converted_mapping[product_code].append({
                        'supplier_id': supplier_id,
                        'share': item.get('share', 1.0)
                    })
                else:
                    print(f"   ⚠️ {idx}. satırda product_code veya supplier_id eksik: {item.keys() if isinstance(item, dict) else 'not dict'}")
            elif isinstance(item, list):
                # nested list olabilir
                for sub_item in item:
                    if isinstance(sub_item, dict):
                        product_code = sub_item.get('product_code') or sub_item.get('Ürün Kodu')
                        supplier_id = sub_item.get('supplier_id') or sub_item.get('Tedarikçi Kodu')
                        if product_code and supplier_id:
                            if product_code not in converted_mapping:
                                converted_mapping[product_code] = []
                            converted_mapping[product_code].append({
                                'supplier_id': supplier_id,
                                'share': sub_item.get('share', 1.0)
                            })
        supplier_mapping = converted_mapping
        print(f"   dönüştürüldü: {len(supplier_mapping)} ürün")
    elif not isinstance(supplier_mapping, dict):
        print(f"   ⚠️ supplier_mapping bilinmeyen tip: {type(supplier_mapping)}")
        supplier_mapping = {}
    
    print(f"🔍 supplier_mapping (son): type={type(supplier_mapping)}, len={len(supplier_mapping)}")
    if supplier_mapping and isinstance(supplier_mapping, dict):
        first_key = next(iter(supplier_mapping.keys()))
        print(f"   ilk ürün: {first_key} -> {len(supplier_mapping.get(first_key, []))} tedarikçi")
        print(f"   ilk ürün detay: {supplier_mapping.get(first_key, [])[:2]}")

    # ============================================================
    # ✅ WEEK_COLUMNS - normalized_data'dan al
    # ============================================================
    week_columns = normalized_data.get('week_columns', [])
    print(f"🔍 week_columns: type={type(week_columns)}, len={len(week_columns)}")
    if week_columns:
        print(f"   week_columns: {week_columns[:5]}...")
    else:
        # materials içinden W kolonlarını bul
        if materials and isinstance(materials, list):
            first_material = materials[0] if materials else {}
            if isinstance(first_material, dict):
                print(f"   materials içinden W kolonları aranıyor...")
                week_cols_from_materials = [k for k in first_material.keys() if k.startswith('W')]
                if week_cols_from_materials:
                    week_columns = week_cols_from_materials
                    print(f"   materials'den bulundu: {week_cols_from_materials}")
                else:
                    # historical_demand veya weekly_data'dan al
                    weekly_data = first_material.get('weekly_data', [])
                    if weekly_data:
                        week_columns = [f'W{i}' for i in range(1, len(weekly_data) + 1)]
                        print(f"   weekly_data'dan türetildi: {len(week_columns)} kolon")

    # ============================================================
    # ✅ cached_data HAZIRLA
    # ============================================================
    cached_data_for_builder = {
        'materials': materials,
        'suppliers': suppliers,
        'supplier_mapping': supplier_mapping,
        'week_columns': week_columns,
        'upload_id': upload_id
    }
    
    print(f"🔍 cached_data_for_builder:")
    print(f"   materials: {len(cached_data_for_builder['materials'])} satır")
    print(f"   suppliers: {len(cached_data_for_builder['suppliers'])} tedarikçi")
    print(f"   supplier_mapping: {len(cached_data_for_builder['supplier_mapping'])} ürün")
    print(f"   week_columns: {len(cached_data_for_builder['week_columns'])} kolon")

    # Dataset Builder ile dataset oluştur
    builder = DatasetBuilder(db)
    
    try:
        dataset = builder.build_from_materials(
            user_id=current_user.id,
            materials=cached_data_for_builder['materials'],
            suppliers=cached_data_for_builder['suppliers'],
            supplier_mapping=cached_data_for_builder['supplier_mapping'],
            week_columns=cached_data_for_builder['week_columns'],
            upload_id=upload_id,
            source_type="excel",
            source_name=cache_data.get('file_name', 'unknown.xlsx'),
            validation_result=cache_data
        )
        
        # ============================================================
        # ✅ Dataset kaydettikten sonra kontrol
        # ============================================================
        print(f"🔍 Dataset kaydedildi: ID={dataset.id}")
        print(f"   dataset_data keys: {list(dataset.dataset_data.keys())}")
        print(f"   suppliers: {type(dataset.dataset_data.get('suppliers'))} - {len(dataset.dataset_data.get('suppliers', {}))}")
        print(f"   supplier_mapping: {type(dataset.dataset_data.get('supplier_mapping'))} - {len(dataset.dataset_data.get('supplier_mapping', {}))}")
        print(f"   week_columns: {len(dataset.dataset_data.get('week_columns', []))}")
        
        # Active Dataset'i güncelle
        active_service = get_active_dataset_service(db)
        active_service.set_active_dataset(current_user.id, dataset.id)
        
        # Cache'i temizle
        delete_cache(upload_id)
        
        return {
            'success': True,
            'dataset_id': dataset.id,
            'message': 'Dataset başarıyla oluşturuldu ve aktif yapıldı'
        }
        
    except ValueError as e:
        print(f"❌ Dataset oluşturma hatası (ValueError): {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Dataset oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Dataset oluşturulurken hata oluştu: {str(e)}")
    
# ============================================================
# 4. GET VALIDATION RESULT
# ============================================================
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


# ============================================================
# 5. CLEAR CACHE
# ============================================================
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