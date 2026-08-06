# app/services/validation_engine.py
"""
Validation Engine - 6 adım validation, structural, missing data, data type, business rules.
Normalizasyon burada yapılmaz, sadece tespit edilir.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import *
from app.schemas.canonical import (
    CANONICAL_MAP, 
    FIELD_TYPES, 
    SHEET_FIELDS, 
    CRITICAL_FIELDS,
    OPTIONAL_FIELDS,  # ✅ EKLENDI
    get_canonical_field, 
    get_excel_column,
    normalize_column_name,
)

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Veri Doğrulama Motoru - 6 adım kontrol
    """

    # Sheet adları (Excel'deki)
    SHEET_NAMES = {
        'materials': 'Temel_Veriler',
        'suppliers': 'Tedarikciler',
        'supplier_mapping': 'Malzeme_Tedarikciler',
    }

    def __init__(self, db: Session, user_id: int, upload_id: str):
        self.db = db
        self.user_id = user_id
        self.upload_id = upload_id
        self.impact_rules = self._load_impact_rules()

    def _load_impact_rules(self) -> List[AnalysisImpactRule]:
        return self.db.query(AnalysisImpactRule).filter(
            AnalysisImpactRule.is_active == True
        ).all()

    # ============================================================
    # STEP 1: Dosya Bilgileri
    # ============================================================
    def get_file_info(self, file_name: str, file_size: int, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """Dosya bilgilerini topla"""
        normalized_sheets = self._normalize_sheets(sheets)
        total_rows = 0
        total_cols = 0
        for sheet_name, rows in normalized_sheets.items():
            total_rows += len(rows)
            if rows and isinstance(rows[0], dict):
                total_cols = max(total_cols, len(rows[0]))
        return {
            'file_name': file_name,
            'file_size': file_size,
            'sheet_count': len(normalized_sheets),
            'total_rows': total_rows,
            'total_cols': total_cols,
            'sheets': list(normalized_sheets.keys())
        }

    # ============================================================
    # STEP 2: Sheet Kontrolü (Yapısal)
    # ============================================================
    def check_sheets(self, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """Gerekli sheet'lerin varlığını kontrol et (structural)"""
        # Önce sheets'i normalize et
        normalized = self._normalize_sheets(sheets)
        sheet_names = list(normalized.keys())
        required_sheets = list(self.SHEET_NAMES.values())

        results = []
        missing = []
        found = []

        for required in required_sheets:
            exists = required in sheet_names
            if exists:
                found.append(required)
            else:
                missing.append(required)
            results.append({
                'sheet': required,
                'exists': exists,
                'status': 'success' if exists else 'error',
                'message': f"'{required}' sheet'i bulundu." if exists else f"'{required}' sheet'i bulunamadı."
            })

        success = len(missing) == 0
        
        # 🔍 DEBUG
        print(f"🔍 Sheet kontrolü sonucu:")
        print(f"   Mevcut sheet'ler: {sheet_names}")
        print(f"   Gerekli: {required_sheets}")
        print(f"   Eksik: {missing}")
        print(f"   Başarılı: {success}")

        return {
            'success': success,
            'found': found,
            'missing': missing,
            'results': results,
            'summary': f"{len(found)}/{len(required_sheets)} sheet bulundu.",
            'can_proceed': success
        }
    
    # ============================================================
    # STEP 3: Veri Kalitesi - Kapsamlı Validation
    # ============================================================

    def validate_data_quality(self, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Veri kalitesi kontrolü:
        - Structural missing field (kolon yok veya tamamen boş)
        - Row-level missing data (coverage)
        - Data type validation
        - Business rule validation
        """
        normalized = self._normalize_sheets(sheets)

        # Sonuç yapıları
        structural_errors = []      # kolon yok veya tamamen boş
        missing_data = []           # satır bazlı eksikler (coverage)
        data_type_errors = []       # tip uyumsuzlukları
        business_rule_errors = []   # iş kuralı ihlalleri
        normalization_suggestions = []  # belirsiz numeric formatlar

        can_proceed = True

        # Her sheet için işle
        for sheet_name, rows in normalized.items():
            if not rows:
                # Sheet boşsa structural error
                structural_errors.append({
                    'sheet': sheet_name,
                    'type': 'structural',
                    'severity': 'critical',
                    'message': f"'{sheet_name}' sheet'i tamamen boş.",
                    'auto_fixable': False,
                    'requires_user_action': True
                })
                can_proceed = False
                continue

            print(f"🔍 {sheet_name} - {len(rows)} satır")
            if rows:
                print(f"   İlk satır anahtarları: {list(rows[0].keys())}")

            # ============================================================
            # 1. STRUCTURAL VALIDATION - Kolonların varlığını kontrol et
            # ============================================================
            
            # Mevcut kolonlar
            existing_columns = list(rows[0].keys()) if rows else []
            print(f"🔍 Mevcut kolonlar: {existing_columns}")
            
            # Beklenen alanlar (canonical isimler)
            expected_fields = SHEET_FIELDS.get(sheet_name, [])
            print(f"🔍 Beklenen alanlar: {expected_fields}")
            
            for field in expected_fields:
                # ============================================================
                # Field'ın mevcut olup olmadığını kontrol et
                # Önce canonical isimle (product_code), sonra orijinal isimle (code) kontrol et
                # ============================================================
                field_exists = False
                matched_column = None
                
                # 1. Canonical isimle kontrol et (product_code)
                if field in existing_columns:
                    field_exists = True
                    matched_column = field
                    print(f"✅ '{field}' canonical isimle bulundu")
                else:
                    # 2. Orijinal isimle kontrol et (code -> Ürün Kodu)
                    original_name = get_excel_column(field)
                    if original_name in existing_columns:
                        field_exists = True
                        matched_column = original_name
                        print(f"✅ '{field}' -> '{original_name}' orijinal isimle bulundu")
                    else:
                        # 3. Tüm kolonları normalize ederek kontrol et
                        field_normalized = normalize_column_name(field)
                        for col in existing_columns:
                            col_normalized = normalize_column_name(col)
                            if col_normalized == field_normalized:
                                field_exists = True
                                matched_column = col
                                print(f"✅ '{field}' -> '{col}' normalize edilmiş eşleşme")
                                break
                
                if not field_exists:
                    # Kolon hiç yok -> structural error
                    structural_errors.append({
                        'sheet': sheet_name,
                        'column': get_excel_column(field),
                        'canonical_field': field,
                        'type': 'structural_missing_column',
                        'severity': 'critical' if field in CRITICAL_FIELDS.get(sheet_name, []) else 'warning',
                        'message': f"'{get_excel_column(field)}' kolonu bulunamadı.",
                        'auto_fixable': False,
                        'requires_user_action': True
                    })
                    if field in CRITICAL_FIELDS.get(sheet_name, []):
                        can_proceed = False
                    continue
                
                # ============================================================
                # Kolon var ama tamamen boş mu kontrol et
                # ============================================================
                all_empty = True
                for row in rows:
                    # Önce canonical isimle dene (product_code)
                    value = row.get(field)
                    if value is None:
                        # Sonra orijinal isimle dene (Ürün Kodu)
                        original_name = get_excel_column(field)
                        value = row.get(original_name)
                    if value is None:
                        # Sonra eşleşen kolon ismiyle dene
                        if matched_column and matched_column != field:
                            value = row.get(matched_column)
                    
                    if not self._is_empty(value):
                        all_empty = False
                        break
                
                if all_empty and len(rows) > 0:
                    # Kolon tamamen boş -> structural error
                    structural_errors.append({
                        'sheet': sheet_name,
                        'column': get_excel_column(field),
                        'canonical_field': field,
                        'type': 'structural_empty_column',
                        'severity': 'critical' if field in CRITICAL_FIELDS.get(sheet_name, []) else 'warning',
                        'message': f"'{get_excel_column(field)}' kolonu tamamen boş.",
                        'coverage_percentage': 0.0,
                        'auto_fixable': False,
                        'requires_user_action': True
                    })
                    if field in CRITICAL_FIELDS.get(sheet_name, []):
                        can_proceed = False

            # ============================================================
            # 2. ROW-LEVEL MISSING DATA (coverage hesaplama)
            # ============================================================
            
            # Opsiyonel alanları al
            optional_fields = OPTIONAL_FIELDS.get(sheet_name, [])
            
            for field in expected_fields:
                # Opsiyonel alanları atla (coverage kontrolü yapma)
                if field in optional_fields:
                    print(f"ℹ️ '{field}' opsiyonel alan, coverage kontrolü yapılmıyor")
                    continue
                
                # Bu field için mevcut kolon adını bul
                actual_column = None
                if field in existing_columns:
                    actual_column = field
                else:
                    original_name = get_excel_column(field)
                    if original_name in existing_columns:
                        actual_column = original_name
                    else:
                        field_normalized = normalize_column_name(field)
                        for col in existing_columns:
                            if normalize_column_name(col) == field_normalized:
                                actual_column = col
                                break
                
                if not actual_column:
                    continue
                
                # İstatistikler
                total_rows = len(rows)
                valid_rows = 0
                missing_count = 0
                missing_rows_list = []
                
                for row_idx, row in enumerate(rows):
                    value = row.get(actual_column)
                    if self._is_empty(value):
                        missing_count += 1
                        missing_rows_list.append(row_idx + 1)
                    else:
                        valid_rows += 1
                
                coverage_percentage = (valid_rows / total_rows * 100) if total_rows > 0 else 0.0
                
                # Sadece coverage %100 değilse ve field critical ise uyarı göster
                if coverage_percentage < 100:
                    is_critical = field in CRITICAL_FIELDS.get(sheet_name, [])
                    
                    if is_critical:
                        severity = 'critical'
                        missing_data.append({
                            'sheet': sheet_name,
                            'column': get_excel_column(field),
                            'canonical_field': field,
                            'type': 'missing_data',
                            'severity': severity,
                            'message': f"'{get_excel_column(field)}' kolonunda {missing_count} satır eksik. (Kapsama: %{coverage_percentage:.1f})",
                            'total_rows': total_rows,
                            'valid_rows': valid_rows,
                            'missing_rows': missing_count,
                            'coverage_percentage': coverage_percentage,
                            'missing_rows_list': missing_rows_list[:50],
                            'auto_fixable': False,
                            'requires_user_action': True
                        })
                        can_proceed = False
                    elif coverage_percentage < 50:
                        severity = 'warning'
                        missing_data.append({
                            'sheet': sheet_name,
                            'column': get_excel_column(field),
                            'canonical_field': field,
                            'type': 'missing_data',
                            'severity': severity,
                            'message': f"'{get_excel_column(field)}' kolonunda {missing_count} satır eksik. (Kapsama: %{coverage_percentage:.1f})",
                            'total_rows': total_rows,
                            'valid_rows': valid_rows,
                            'missing_rows': missing_count,
                            'coverage_percentage': coverage_percentage,
                            'missing_rows_list': missing_rows_list[:50],
                            'auto_fixable': False,
                            'requires_user_action': True
                        })

            # ============================================================
            # 3. DATA TYPE VALIDATION
            # ============================================================
            
            # Duplicate kontrolü için set
            seen_errors = set()
            
            for field in expected_fields:
                actual_column = None
                if field in existing_columns:
                    actual_column = field
                else:
                    original_name = get_excel_column(field)
                    if original_name in existing_columns:
                        actual_column = original_name
                    else:
                        field_normalized = normalize_column_name(field)
                        for col in existing_columns:
                            if normalize_column_name(col) == field_normalized:
                                actual_column = col
                                break
                
                if not actual_column:
                    continue
                
                expected_type = FIELD_TYPES.get(field)
                if not expected_type:
                    continue
                
                is_optional = field in OPTIONAL_FIELDS.get(sheet_name, [])
                
                for row_idx, row in enumerate(rows):
                    value = row.get(actual_column)
                    
                    # Boş değerler opsiyonel alanlarda tolere edilir
                    if self._is_empty(value):
                        continue
                    
                    # Tip kontrolü
                    is_valid, error_msg = self._validate_type(value, expected_type, field)
                    if not is_valid:
                        # Opsiyonel alanlarda geçersiz değer WARNING olur, ama GÖSTERİLİR!
                        severity = 'critical' if field in CRITICAL_FIELDS.get(sheet_name, []) else 'warning'
                        
                        # Opsiyonel alanlarda geçersiz değer warning
                        if is_optional:
                            severity = 'warning'
                        
                        # Duplicate kontrolü
                        error_key = f"{sheet_name}_{row_idx}_{field}_{value}"
                        if error_key in seen_errors:
                            continue
                        seen_errors.add(error_key)
                        
                        data_type_errors.append({
                            'sheet': sheet_name,
                            'row': row_idx + 1,
                            'column': get_excel_column(field),
                            'canonical_field': field,
                            'original_value': value,
                            'expected_type': expected_type,
                            'type': 'data_type_error',
                            'severity': severity,
                            'message': error_msg,
                            'auto_fixable': False,
                            'requires_user_action': True
                        })
                        if severity == 'critical':
                            can_proceed = False
                    
                    # Normalization suggestion (belirsiz numeric format)
                    if expected_type in ['float', 'percentage'] and isinstance(value, str):
                        normalized, is_ambiguous = self._suggest_normalization(value)
                        if is_ambiguous:
                            # Duplicate kontrolü
                            sugg_key = f"{sheet_name}_{row_idx}_{field}_{value}"
                            if sugg_key not in seen_errors:
                                seen_errors.add(sugg_key)
                                normalization_suggestions.append({
                                    'sheet': sheet_name,
                                    'row': row_idx + 1,
                                    'column': get_excel_column(field),
                                    'canonical_field': field,
                                    'original_value': value,
                                    'suggested_value': normalized,
                                    'type': 'normalization_suggestion',
                                    'severity': 'info',
                                    'message': f"Belirsiz format: '{value}'. Önerilen: '{normalized}'. Lütfen onaylayın veya düzeltin.",
                                    'auto_fixable': False,
                                    'requires_user_action': True
                                })

            # ============================================================
            # 4. BUSINESS RULE VALIDATION
            # ============================================================
            
            # 4a. Temel_Veriler için: Ürün Kodu boş olan satırlar
            if sheet_name == 'Temel_Veriler':
                # Ürün Kodu kolonunu canonical helper ile bul
                code_column = None
                for col in existing_columns:
                    if normalize_column_name(col) == 'productcode':
                        code_column = col
                        break
                    if col == 'product_code' or col == 'code':
                        code_column = col
                        break
                
                if code_column:
                    for row_idx, row in enumerate(rows):
                        code = row.get(code_column)
                        if code is None or str(code).strip() == '':
                            business_rule_errors.append({
                                'sheet': sheet_name,
                                'row': row_idx + 1,
                                'column': 'Ürün Kodu',
                                'canonical_field': 'product_code',
                                'original_value': None,
                                'type': 'business_rule',
                                'severity': 'critical',
                                'message': f"{row_idx + 1}. satırda Ürün Kodu boş! Lütfen doldurun.",
                                'auto_fixable': False,
                                'requires_user_action': True
                            })
                            can_proceed = False
                            print(f"⚠️ {row_idx + 1}. satırda Ürün Kodu BOŞ - Kritik hata!")

            # 4b. Tedarikciler için: Tedarikçi Kodu boş olan satırlar
            if sheet_name == 'Tedarikciler':
                supplier_column = None
                if 'Tedarikçi Kodu' in existing_columns:
                    supplier_column = 'Tedarikçi Kodu'
                elif 'supplier_id' in existing_columns:
                    supplier_column = 'supplier_id'
                else:
                    for col in existing_columns:
                        if normalize_column_name(col) in ['supplier_id', 'tedarikci_kodu']:
                            supplier_column = col
                            break
                
                if supplier_column:
                    for row_idx, row in enumerate(rows):
                        supplier_code = row.get(supplier_column)
                        if supplier_code is None or str(supplier_code).strip() == '':
                            business_rule_errors.append({
                                'sheet': sheet_name,
                                'row': row_idx + 1,
                                'column': 'Tedarikçi Kodu',
                                'canonical_field': 'supplier_id',
                                'original_value': None,
                                'type': 'business_rule',
                                'severity': 'critical',
                                'message': f"{row_idx + 1}. satırda Tedarikçi Kodu boş! Lütfen doldurun.",
                                'auto_fixable': False,
                                'requires_user_action': True
                            })
                            can_proceed = False

            # 4c. Negative values - SADECE KRİTİK/OPTİSYONEL OLMAYAN ALANLAR
            numeric_fields = ['initial_stock', 'lead_time_days', 'eoq', 'unit_cost', 'shortage_cost', 'lt_mean', 'lt_std']
            optional_fields = OPTIONAL_FIELDS.get(sheet_name, [])
            
            for field in numeric_fields:
                # Opsiyonel alanları atla
                if field in optional_fields:
                    continue
                
                if field not in expected_fields:
                    continue
                
                actual_column = None
                if field in existing_columns:
                    actual_column = field
                else:
                    original_name = get_excel_column(field)
                    if original_name in existing_columns:
                        actual_column = original_name
                
                if not actual_column:
                    continue
                
                for row_idx, row in enumerate(rows):
                    value = row.get(actual_column)
                    if not self._is_empty(value):
                        try:
                            num = float(value)
                            if num < 0:
                                business_rule_errors.append({
                                    'sheet': sheet_name,
                                    'row': row_idx + 1,
                                    'column': get_excel_column(field),
                                    'canonical_field': field,
                                    'original_value': value,
                                    'type': 'business_rule',
                                    'severity': 'critical',
                                    'message': f"{get_excel_column(field)} negatif olamaz. Değer: {value}",
                                    'auto_fixable': False,
                                    'requires_user_action': True
                                })
                                can_proceed = False
                        except:
                            pass

            # 4d. Percentage ranges (0-100) - SADECE KRİTİK/OPTİSYONEL OLMAYAN ALANLAR
            percentage_fields = ['holding_rate', 'ontime_rate', 'share']
            for field in percentage_fields:
                # Opsiyonel alanları atla
                if field in optional_fields:
                    continue
                
                if field not in expected_fields:
                    continue
                
                actual_column = None
                if field in existing_columns:
                    actual_column = field
                else:
                    original_name = get_excel_column(field)
                    if original_name in existing_columns:
                        actual_column = original_name
                
                if not actual_column:
                    continue
                
                for row_idx, row in enumerate(rows):
                    value = row.get(actual_column)
                    if not self._is_empty(value):
                        try:
                            num = float(value)
                            if num < 0 or num > 100:
                                business_rule_errors.append({
                                    'sheet': sheet_name,
                                    'row': row_idx + 1,
                                    'column': get_excel_column(field),
                                    'canonical_field': field,
                                    'original_value': value,
                                    'type': 'business_rule',
                                    'severity': 'warning',
                                    'message': f"{get_excel_column(field)} %{value} (0-100 arası olmalı)",
                                    'auto_fixable': False,
                                    'requires_user_action': True
                                })
                        except:
                            pass

            # 4e. Duplicate product_code (Temel_Veriler)
            if sheet_name == 'Temel_Veriler':
                code_column = None
                if 'code' in existing_columns:
                    code_column = 'code'
                elif 'Ürün Kodu' in existing_columns:
                    code_column = 'Ürün Kodu'
                
                if code_column:
                    product_codes = {}
                    for row_idx, row in enumerate(rows):
                        code = row.get(code_column)
                        if not self._is_empty(code):
                            code_str = str(code).strip()
                            if code_str in product_codes:
                                product_codes[code_str].append(row_idx + 1)
                            else:
                                product_codes[code_str] = [row_idx + 1]
                    
                    for code, rows_list in product_codes.items():
                        if len(rows_list) > 1:
                            business_rule_errors.append({
                                'sheet': sheet_name,
                                'column': 'Ürün Kodu',
                                'canonical_field': 'product_code',
                                'value': code,
                                'type': 'business_rule',
                                'severity': 'critical',
                                'message': f"Ürün kodu '{code}' birden fazla satırda tekrar ediyor.",
                                'rows': rows_list,
                                'auto_fixable': False,
                                'requires_user_action': True
                            })
                            can_proceed = False

            # 4f. Duplicate supplier_id (Tedarikciler)
            if sheet_name == 'Tedarikciler':
                supplier_column = None
                if 'Tedarikçi Kodu' in existing_columns:
                    supplier_column = 'Tedarikçi Kodu'
                elif 'supplier_id' in existing_columns:
                    supplier_column = 'supplier_id'
                
                if supplier_column:
                    supplier_ids = {}
                    for row_idx, row in enumerate(rows):
                        sid = row.get(supplier_column)
                        if not self._is_empty(sid):
                            sid_str = str(sid).strip()
                            if sid_str in supplier_ids:
                                supplier_ids[sid_str].append(row_idx + 1)
                            else:
                                supplier_ids[sid_str] = [row_idx + 1]
                    
                    for sid, rows_list in supplier_ids.items():
                        if len(rows_list) > 1:
                            business_rule_errors.append({
                                'sheet': sheet_name,
                                'column': 'Tedarikçi Kodu',
                                'canonical_field': 'supplier_id',
                                'value': sid,
                                'type': 'business_rule',
                                'severity': 'critical',
                                'message': f"Tedarikçi kodu '{sid}' birden fazla satırda tekrar ediyor.",
                                'rows': rows_list,
                                'auto_fixable': False,
                                'requires_user_action': True
                            })
                            can_proceed = False

        # ============================================================
        # Hataları kategorilere ayır (Step 4 için)
        # ============================================================
        critical_errors = []
        warnings = []
        info_messages = []
        
        for err in structural_errors:
            if err.get('severity') == 'critical':
                critical_errors.append(err)
            else:
                warnings.append(err)
        
        for err in business_rule_errors:
            if err.get('severity') == 'critical':
                critical_errors.append(err)
            else:
                warnings.append(err)
        
        for err in data_type_errors:
            if err.get('severity') == 'critical':
                critical_errors.append(err)
            else:
                warnings.append(err)
        
        for err in missing_data:
            if err.get('severity') == 'critical':
                critical_errors.append(err)
            else:
                warnings.append(err)
        
        for err in normalization_suggestions:
            info_messages.append(err)
        
        # Özet
        total_structural = len(structural_errors)
        total_missing = len(missing_data)
        total_type_errors = len(data_type_errors)
        total_business = len(business_rule_errors)
        total_suggestions = len(normalization_suggestions)
        total_critical = len(critical_errors)
        total_warnings = len(warnings)
        total_info = len(info_messages)
        
        # ✅ normalized bir dict olduğundan emin ol
        total_rows = 0
        if isinstance(normalized, dict):
            for rows in normalized.values():
                if isinstance(rows, list):
                    total_rows += len(rows)

        total_problems = total_structural + total_missing + total_type_errors + total_business
        score = max(0, 100 - total_problems * 5)

        return {
            'structural_errors': structural_errors,
            'missing_data': missing_data,
            'data_type_errors': data_type_errors,
            'business_rule_errors': business_rule_errors,
            'normalization_suggestions': normalization_suggestions,
            'critical_errors': critical_errors,
            'warnings': warnings,
            'info_messages': info_messages,
            'summary': {
                'total_structural': total_structural,
                'total_missing': total_missing,
                'total_type_errors': total_type_errors,
                'total_business': total_business,
                'total_suggestions': total_suggestions,
                'total_critical': total_critical,
                'total_warnings': total_warnings,
                'total_info': total_info,
                'total_rows': total_rows,
                'score': score,
            },
            'can_proceed': can_proceed
        }

    def _normalize_column_name(self, column_name: str) -> str:
        """Kolon adını normalize eder (küçük harf, Türkçe karakterler, boşluklar)"""
        if not column_name:
            return ''
        # Küçük harfe çevir
        normalized = column_name.lower()
        # Türkçe karakterleri değiştir
        replacements = {
            'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
            'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
        }
        for tr, en in replacements.items():
            normalized = normalized.replace(tr, en)
        # Parantez içindekileri temizle
        normalized = re.sub(r'\([^)]*\)', '', normalized)
        # Özel karakterleri temizle (sadece harf ve rakam kalır)
        normalized = re.sub(r'[^a-z0-9]', '', normalized)
        return normalized

    # ============================================================
    # STEP 5: Analysis Impact Assessment
    # ============================================================
    def analyze_impact(self, sheets: Dict[str, Any], validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analysis Impact Assessment - Hangi analizlerin nasıl etkilendiğini hesaplar.
        Mevcut analysis_impact_rules tablosunu kullanır.
        """
        normalized = self._normalize_sheets(sheets)
        # Mevcut impact rules
        rules = self.impact_rules
        if not rules:
            # Varsayılan kurallar (hardcoded fallback)
            rules = self._get_default_rules()

        # Her analiz için skor hesapla
        analysis_scores = {}
        analysis_results = {}

        # Validation sonuçlarından kritik hataları al
        critical_errors = validation_results.get('structural_errors', []) + \
                          validation_results.get('missing_data', []) + \
                          validation_results.get('data_type_errors', []) + \
                          validation_results.get('business_rule_errors', [])
        critical_errors = [e for e in critical_errors if e.get('severity') == 'critical']

        # Her analiz tipi için
        analysis_types = set(r.analysis_type for r in rules)
        for analysis_type in analysis_types:
            score = 100
            impacts = []
            relevant_rules = [r for r in rules if r.analysis_type == analysis_type]

            for rule in relevant_rules:
                field = rule.field_name  # canonical field adı
                importance = rule.importance
                # Bu alanla ilgili kritik hata var mı?
                field_errors = [e for e in critical_errors if e.get('canonical_field') == field]
                if field_errors:
                    # Skoru düşür
                    penalty = 20 if importance == 'critical' else 10 if importance == 'recommended' else 5
                    score -= penalty * len(field_errors)
                    for err in field_errors:
                        impacts.append({
                            'field': field,
                            'importance': importance,
                            'status': 'missing',
                            'message': err.get('message', ''),
                            'recommendation': f"{field} alanını düzeltin.",
                            'problem': err.get('message', ''),
                            'reason': self._get_impact_reason(analysis_type, field),
                            'affected_analyses': [analysis_type],
                            'expected_result': self._get_expected_result(analysis_type, field),
                            'recommendation': f"{field} alanını düzeltin."
                        })
                else:
                    impacts.append({
                        'field': field,
                        'importance': importance,
                        'status': 'ok',
                        'message': f"{field} alanı mevcut.",
                        'recommendation': None
                    })

            # Coverage bazında ek etki (varsa)
            for missing in validation_results.get('missing_data', []):
                if missing.get('canonical_field') in [r.field_name for r in relevant_rules]:
                    coverage = missing.get('coverage_percentage', 0)
                    if coverage < 80:
                        score -= 5
                        impacts.append({
                            'field': missing['canonical_field'],
                            'importance': 'recommended',
                            'status': 'partial',
                            'message': f"Coverage %{coverage:.1f}",
                            'recommendation': f"Eksik verileri tamamlayın.",
                            'problem': f"Veri kapsamı düşük (%{coverage:.1f})",
                            'reason': self._get_impact_reason(analysis_type, missing['canonical_field']),
                            'affected_analyses': [analysis_type],
                            'expected_result': self._get_expected_result(analysis_type, missing['canonical_field']),
                            'recommendation': f"Eksik verileri tamamlayın."
                        })

            score = max(0, min(100, score))
            analysis_scores[analysis_type] = score
            analysis_results[analysis_type] = impacts

        # Detailed impacts (UI için)
        detailed_impacts = []
        for analysis_type, impacts in analysis_results.items():
            for imp in impacts:
                if imp.get('status') in ['missing', 'partial']:
                    detailed_impacts.append({
                        'analysis': analysis_type,
                        'field': imp.get('field'),
                        'importance': imp.get('importance'),
                        'problem': imp.get('problem', imp.get('message', '')),
                        'reason': imp.get('reason', ''),
                        'affected_analyses': imp.get('affected_analyses', [analysis_type]),
                        'expected_result': imp.get('expected_result', ''),
                        'recommendation': imp.get('recommendation', '')
                    })

        overall_score = sum(analysis_scores.values()) / len(analysis_scores) if analysis_scores else 0

        # AI yorumu (basit template)
        if overall_score >= 90:
            ai_comment = "Dataset analiz için uygundur. Tüm analizler başarıyla çalıştırılabilir."
        elif overall_score >= 70:
            ai_comment = "Dataset analiz için kısmen uygundur. Bazı analizlerde doğruluk kaybı yaşanabilir."
        elif overall_score >= 50:
            ai_comment = "Dataset analiz için sınırlı uygundur. Eksik alanlar tamamlanmalıdır."
        else:
            ai_comment = "Dataset analiz için uygun değildir. Kritik alanlar eksiktir."

        ai_recommendation = f"Veri seti hazırlık skoru: %{overall_score:.0f}. {ai_comment}"

        return {
            'analysis_scores': analysis_scores,
            'analysis_results': analysis_results,
            'detailed_impacts': detailed_impacts,
            'ai_comment': ai_comment,
            'ai_recommendation': ai_recommendation,
            'overall_score': overall_score
        }

    # ============================================================
    # YARDIMCI FONKSİYONLAR
    # ============================================================

# app/services/validation_engine.py - _normalize_sheets DÜZELTİLDİ (KESİN ÇÖZÜM)

    def _normalize_sheets(self, sheets: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """ExcelReader'dan gelen veriyi standart formata çevirir."""
        normalized = {}
        
        for key, data in sheets.items():
            sheet_name = self.SHEET_NAMES.get(key, key)
            
            if key == 'supplier_mapping' and isinstance(data, dict):
                rows = []
                print(f"🔍 supplier_mapping işleniyor: {len(data)} ürün")
                
                for product_code, supplier_list in data.items():
                    if not isinstance(supplier_list, list):
                        print(f"⚠️ supplier_list liste değil: {type(supplier_list)} - atlanıyor")
                        continue
                    
                    for item in supplier_list:
                        if not isinstance(item, dict):
                            print(f"⚠️ item dict değil: {type(item)} - {item}")
                            continue
                        
                        # ✅ supplier_id'yi al
                        supplier_id = item.get('supplier_id')
                        if supplier_id is None:
                            print(f"⚠️ supplier_id bulunamadı, item: {item}")
                            continue
                        
                        # ✅ share değerini al
                        share = item.get('share', 1.0)
                        if share is None:
                            share = 1.0
                        
                        # ✅ open_qty değerini al
                        open_qty = item.get('open_qty', 0)
                        if open_qty is None:
                            open_qty = 0
                        
                        # ✅ planned_due değerini al
                        planned_due = item.get('planned_due', '')
                        
                        # ============================================================
                        # ✅ SADECE BELİRTİLEN KOLONLARI EKLE
                        # ============================================================
                        row = {
                            'Ürün Kodu': str(product_code) if product_code else '',
                            'Tedarikçi Kodu': str(supplier_id) if supplier_id else '',
                            'Tedarik Payı (%)': float(share) * 100 if share else 0,
                            'Açık Sipariş': float(open_qty) if open_qty else 0,
                            'Planlanan Teslim Tarihi': str(planned_due) if planned_due else '',
                        }
                        rows.append(row)
                
                normalized[sheet_name] = rows
                print(f"🔍 supplier_mapping normalize edildi: {len(rows)} satır")
                
            elif key == 'suppliers' and isinstance(data, dict):
                rows = []
                print(f"🔍 suppliers işleniyor: {len(data)} tedarikçi")
                
                for supplier_code, supplier_data in data.items():
                    if not isinstance(supplier_data, dict):
                        print(f"⚠️ supplier_data dict değil: {type(supplier_data)} - {supplier_data}")
                        continue
                    
                    # ============================================================
                    # ✅ SADECE BELİRTİLEN KOLONLARI EKLE
                    # ============================================================
                    row = {
                        'Tedarikçi Kodu': str(supplier_code) if supplier_code else '',
                        'Tedarikçi Adı': str(supplier_data.get('name', '')),
                        'Tedarikçi Faktörü': float(supplier_data.get('factor', 1.0)),
                        'Zamanında Teslim Oranı (%)': float(supplier_data.get('ontime_rate', 0)) * 100,
                        'Ortalama Teslim Süresi (Gün)': float(supplier_data.get('lt_mean', '')) if supplier_data.get('lt_mean') else '',
                        'Teslim Süresi Standart Sapması': float(supplier_data.get('lt_std', '')) if supplier_data.get('lt_std') else '',
                    }
                    rows.append(row)
                
                normalized[sheet_name] = rows
                print(f"🔍 suppliers normalize edildi: {len(rows)} satır")
                
            elif key == 'materials' and isinstance(data, list):
                rows = []
                for row in data:
                    if isinstance(row, dict):
                        rows.append(row)
                normalized[sheet_name] = rows
                print(f"🔍 Temel_Veriler: {len(rows)} satır")
                
            else:
                # Diğer durumlar
                if isinstance(data, list):
                    rows = []
                    for row in data:
                        if isinstance(row, dict):
                            rows.append(row)
                    normalized[sheet_name] = rows
                elif isinstance(data, dict):
                    rows = []
                    for v in data.values():
                        if isinstance(v, list):
                            for row in v:
                                if isinstance(row, dict):
                                    rows.append(row)
                            break
                    normalized[sheet_name] = rows
                else:
                    normalized[sheet_name] = []
        
        return normalized

    def _is_empty(self, value) -> bool:
        """
        Boş değer mi kontrolü.
        - None
        - Boş string ('')
        - Sadece boşluk içeren string ('   ')
        - 0 (sıfır) DEĞERİ BOŞ DEĞİLDİR! (0 geçerli bir sayısal değerdir)
        - 0.0 (sıfır) DEĞERİ BOŞ DEĞİLDİR!
        - NaN (pandas) -> boş
        """
        if value is None:
            return True
        if isinstance(value, float):
            # NaN kontrolü (pandas)
            try:
                import math
                if math.isnan(value):
                    return True
            except:
                pass
            # 0.0 geçerli bir değerdir, boş değil
            return False
        if isinstance(value, int):
            # 0 geçerli bir değerdir, boş değil
            return False
        if isinstance(value, str):
            # Sadece boşluk içeren string'leri boş kabul et
            return value.strip() == ''
        if isinstance(value, list):
            return len(value) == 0
        if isinstance(value, dict):
            return len(value) == 0
        return False
    
# app/services/validation_engine.py - _validate_type içinde

    def _validate_type(self, value, expected_type: str, field: str) -> tuple:
        """Veri tipi doğrulama."""
        if expected_type == 'string':
            return True, ""
        if expected_type == 'float':
            try:
                float(value)
                return True, ""
            except:
                return False, f"'{value}' sayısal bir değer değil."
        if expected_type == 'percentage':
            try:
                # Önce sayısal değere çevir
                num = float(value)
                if 0 <= num <= 100:
                    return True, ""
                else:
                    return False, f"Yüzde değeri 0-100 arası olmalı, '{num}'"
            except:
                return False, f"'{value}' yüzde formatında değil."
        if expected_type == 'date':
            try:
                from datetime import datetime
                datetime.strptime(str(value), "%Y-%m-%d")
                return True, ""
            except:
                try:
                    datetime.strptime(str(value), "%d.%m.%Y")
                    return True, ""
                except:
                    return False, f"'{value}' geçerli bir tarih değil."
        if expected_type == 'list':
            return isinstance(value, list), "Liste olmalı."
        return True, ""
    
    def _suggest_normalization(self, value: str) -> tuple:
            """Belirsiz numeric formatları normalize etmek için öneri üretir."""
            try:
                float(value)
                return value, False
            except:
                pass

            # Türkçe format: 1.250,50 -> 1250.50
            match = re.match(r'^(\d{1,3}(?:\.\d{3})*),(\d{2})$', value)
            if match:
                normalized = match.group(1).replace('.', '') + '.' + match.group(2)
                return normalized, False

            # 125,50 -> 125.50
            match = re.match(r'^(\d+),(\d{2})$', value)
            if match:
                normalized = match.group(1) + '.' + match.group(2)
                return normalized, False

            # 10.000 -> belirsiz
            match = re.match(r'^(\d{1,3}\.\d{3})$', value)
            if match:
                return value, True

            # 10,000 -> belirsiz
            match = re.match(r'^(\d{1,3},\d{3})$', value)
            if match:
                return value, True

            return value, True

    def _get_default_rules(self) -> List[AnalysisImpactRule]:
        """Varsayılan impact kuralları (fallback)."""
        from app.models import AnalysisImpactRule
        rules = []
        default_rules = [
            ('forecast', 'product_code', 'critical'),
            ('forecast', 'historical_demand', 'critical'),
            ('forecast', 'group', 'recommended'),
            ('safety_stock', 'product_code', 'critical'),
            ('safety_stock', 'lead_time_days', 'critical'),
            ('safety_stock', 'historical_demand', 'critical'),
            ('supplier', 'supplier_id', 'critical'),
            ('supplier', 'ontime_rate', 'critical'),
            ('supplier', 'lt_mean', 'recommended'),
            ('simulation', 'product_code', 'critical'),
            ('simulation', 'lead_time_days', 'critical'),
            ('simulation', 'historical_demand', 'critical'),
            ('backtest', 'product_code', 'critical'),
            ('backtest', 'historical_demand', 'critical'),
        ]
        for analysis_type, field_name, importance in default_rules:
            rule = AnalysisImpactRule(
                analysis_type=analysis_type,
                field_name=field_name,
                importance=importance,
                is_active=True
            )
            rules.append(rule)
        return rules

    def _get_impact_reason(self, analysis: str, field: str) -> str:
        reasons = {
            'forecast': {
                'product_code': 'Forecast için ürün bazlı tahmin yapılması gerekir.',
                'historical_demand': 'Talep geçmişi olmadan tahmin üretilemez.',
                'group': 'AI öğrenmesi grup bazında yapılır.',
                'lead_time_days': 'Tedarik süresi tahmin doğruluğunu etkiler.'
            },
            'safety_stock': {
                'product_code': 'Emniyet stoğu ürün bazında hesaplanır.',
                'historical_demand': 'Talep değişkenliği hesaplanamaz.',
                'lead_time_days': 'Teslimat süresi olmadan SS hesaplanamaz.'
            },
            'supplier': {
                'supplier_id': 'Tedarikçi tanımlanmamış.',
                'ontime_rate': 'Tedarikçi performansı değerlendirilemez.',
                'lt_mean': 'Ortalama teslim süresi gerekli.'
            },
            'simulation': {
                'product_code': 'Simülasyon ürün bazında çalışır.',
                'historical_demand': 'Talep dağılımı olmadan simülasyon yapılamaz.',
                'lead_time_days': 'Teslimat süresi simülasyonda kritiktir.'
            },
            'backtest': {
                'product_code': 'Backtest ürün bazında yapılır.',
                'historical_demand': 'Geçmiş veri olmadan backtest yapılamaz.'
            }
        }
        return reasons.get(analysis, {}).get(field, 'Veri eksikliği analizi etkiler.')

    def _get_expected_result(self, analysis: str, field: str) -> str:
        results = {
            'forecast': 'Tahmin doğruluğu azalabilir veya tahmin yapılamayabilir.',
            'safety_stock': 'Emniyet stoğu hesaplanamayabilir veya hatalı olabilir.',
            'supplier': 'Tedarikçi analizi yapılamayabilir.',
            'simulation': 'Simülasyon sonuçları güvenilir olmayabilir.',
            'backtest': 'Backtest sonuçları hatalı olabilir.',
        }
        return results.get(analysis, 'Analiz doğruluğu etkilenir.')


def get_validation_engine(db: Session, user_id: int, upload_id: str) -> ValidationEngine:
    return ValidationEngine(db, user_id, upload_id)
