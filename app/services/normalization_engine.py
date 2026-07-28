# app/services/normalization_engine.py
"""
Normalization Engine - Sadece güvenli numerik normalizasyon yapar.
String alanlara dokunmaz.
Locale-aware: tr-TR varsayılan.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.schemas.canonical import FIELD_TYPES, get_canonical_field

logger = logging.getLogger(__name__)


class NormalizationEngine:
    """
    Akıllı Veri Standardizasyonu Motoru
    - Sadece numerik alanlarda locale-aware dönüşüm
    - Belirsiz formatlarda user action required
    """

    def __init__(self, db: Session, user_id: int, upload_id: str):
        self.db = db
        self.user_id = user_id
        self.upload_id = upload_id

# app/services/normalization_engine.py - DÜZELTİLDİ

    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Veriyi normalize et.
        Sadece numerik alanlarda güvenli dönüşüm yapar.
        String alanlara dokunmaz.
        Validation hatalarını da errors listesine ekler.
        """
        normalized = {}
        changes = []
        suggestions = []
        errors = []

        # ============================================================
        # Validation hatalarını al (data içinden)
        # ============================================================
        validation_errors = data.pop('_validation_errors', [])
        
        # ============================================================
        # Veriyi sheet bazında işle
        # ============================================================
        for sheet_name, rows in data.items():
            if not rows:
                normalized[sheet_name] = []
                continue

            # ============================================================
            # ✅ suppliers DİCT İSE DÖNÜŞTÜRME - YAPISINI KORU
            # ============================================================
            if sheet_name == 'suppliers' and isinstance(rows, dict):
                print(f"🔍 {sheet_name} dict, yapısı korunuyor: {len(rows)} tedarikçi")
                # Sadece değerleri normalize et, yapıyı bozma
                normalized_rows = {}
                for supplier_id, supplier_data in rows.items():
                    if isinstance(supplier_data, dict):
                        new_supplier_data = dict(supplier_data)
                        # Numerik alanları normalize et
                        for col, value in supplier_data.items():
                            if isinstance(value, str):
                                canonical_field = get_canonical_field(col)
                                expected_type = FIELD_TYPES.get(canonical_field)
                                if expected_type in ['float', 'percentage']:
                                    normalized_value, is_ambiguous, suggestion = self._normalize_numeric(value)
                                    if normalized_value != value and not is_ambiguous:
                                        new_supplier_data[col] = normalized_value
                                        changes.append({
                                            'sheet': sheet_name,
                                            'row': supplier_id,
                                            'column': col,
                                            'canonical_field': canonical_field,
                                            'original': value,
                                            'new': normalized_value,
                                            'confidence': 1.0,
                                            'reason': 'Güvenli numerik dönüşüm'
                                        })
                        normalized_rows[supplier_id] = new_supplier_data
                normalized[sheet_name] = normalized_rows
                print(f"🔍 {sheet_name} normalize edildi: {len(normalized_rows)} tedarikçi (dict korundu)")
                continue

            # ============================================================
            # ✅ supplier_mapping DİCT İSE DÖNÜŞTÜRME - YAPISINI KORU
            # ============================================================
            if sheet_name == 'supplier_mapping' and isinstance(rows, dict):
                print(f"🔍 {sheet_name} dict, yapısı korunuyor: {len(rows)} ürün")
                normalized_rows = {}
                for product_code, supplier_list in rows.items():
                    if isinstance(supplier_list, list):
                        new_supplier_list = []
                        for item in supplier_list:
                            if isinstance(item, dict):
                                new_item = dict(item)
                                # Numerik alanları normalize et (share, open_qty)
                                for col, value in item.items():
                                    if isinstance(value, str):
                                        canonical_field = get_canonical_field(col)
                                        expected_type = FIELD_TYPES.get(canonical_field)
                                        if expected_type in ['float', 'percentage']:
                                            normalized_value, is_ambiguous, suggestion = self._normalize_numeric(value)
                                            if normalized_value != value and not is_ambiguous:
                                                new_item[col] = normalized_value
                                                changes.append({
                                                    'sheet': sheet_name,
                                                    'row': product_code,
                                                    'column': col,
                                                    'canonical_field': canonical_field,
                                                    'original': value,
                                                    'new': normalized_value,
                                                    'confidence': 1.0,
                                                    'reason': 'Güvenli numerik dönüşüm'
                                                })
                                new_supplier_list.append(new_item)
                        normalized_rows[product_code] = new_supplier_list
                normalized[sheet_name] = normalized_rows
                print(f"🔍 {sheet_name} normalize edildi: {len(normalized_rows)} ürün (dict korundu)")
                continue

            # ============================================================
            # materials - LİSTE, SATIR BAZLI NORMALİZASYON
            # ============================================================
            if sheet_name == 'materials' and isinstance(rows, list):
                normalized_rows = []
                for row_idx, row in enumerate(rows):
                    if not isinstance(row, dict):
                        print(f"⚠️ {sheet_name} - {row_idx}. satır dict değil: {type(row)} - atlanıyor")
                        continue
                    
                    new_row = dict(row)
                    for col, value in row.items():
                        if isinstance(value, str):
                            canonical_field = get_canonical_field(col)
                            expected_type = FIELD_TYPES.get(canonical_field)
                            if expected_type in ['float', 'percentage']:
                                original = value
                                normalized_value, is_ambiguous, suggestion = self._normalize_numeric(value)
                                if normalized_value != original:
                                    if not is_ambiguous:
                                        new_row[col] = normalized_value
                                        changes.append({
                                            'sheet': sheet_name,
                                            'row': row_idx + 1,
                                            'column': col,
                                            'canonical_field': canonical_field,
                                            'original': original,
                                            'new': normalized_value,
                                            'confidence': 1.0,
                                            'reason': 'Güvenli numerik dönüşüm'
                                        })
                                    else:
                                        suggestions.append({
                                            'sheet': sheet_name,
                                            'row': row_idx + 1,
                                            'column': col,
                                            'canonical_field': canonical_field,
                                            'original': original,
                                            'suggestion': normalized_value,
                                            'confidence': 0.5,
                                            'message': f"Belirsiz format: '{original}'. Önerilen: '{normalized_value}'. Lütfen onaylayın veya düzeltin."
                                        })
                                elif is_ambiguous:
                                    suggestions.append({
                                        'sheet': sheet_name,
                                        'row': row_idx + 1,
                                        'column': col,
                                        'canonical_field': canonical_field,
                                        'original': original,
                                        'suggestion': normalized_value,
                                        'confidence': 0.5,
                                        'message': f"Belirsiz format: '{original}'. Lütfen düzeltin."
                                    })
                    normalized_rows.append(new_row)
                normalized[sheet_name] = normalized_rows
                print(f"🔍 {sheet_name} normalize edildi: {len(normalized_rows)} satır")
                continue

            # ============================================================
            # Diğer sheet'ler (Tedarikciler, Malzeme_Tedarikciler fallback)
            # ============================================================
            # Eğer rows bir dict ise ve yukarıdaki özel durumlara girmediyse
            if isinstance(rows, dict):
                print(f"🔍 {sheet_name} dict, dönüştürülüyor...")
                rows_list = []
                for key, value in rows.items():
                    if isinstance(value, dict):
                        value['_key'] = key
                        rows_list.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item['_key'] = key
                                rows_list.append(item)
                    else:
                        rows_list.append(value)
                rows = rows_list
                print(f"🔍 {sheet_name} dönüştürüldü: {len(rows)} satır")

            # ROWS BİR LİSTE DEĞİLSE ATLA
            if not isinstance(rows, list):
                print(f"⚠️ {sheet_name} rows liste değil: {type(rows)} - atlanıyor")
                normalized[sheet_name] = []
                continue

            # HER SATIRI İŞLE (diğer sheet'ler için)
            normalized_rows = []
            for row_idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    print(f"⚠️ {sheet_name} - {row_idx}. satır dict değil: {type(row)} - atlanıyor")
                    continue
                
                new_row = dict(row)
                for col, value in row.items():
                    if isinstance(value, str):
                        canonical_field = get_canonical_field(col)
                        expected_type = FIELD_TYPES.get(canonical_field)
                        if expected_type in ['float', 'percentage']:
                            original = value
                            normalized_value, is_ambiguous, suggestion = self._normalize_numeric(value)
                            if normalized_value != original:
                                if not is_ambiguous:
                                    new_row[col] = normalized_value
                                    changes.append({
                                        'sheet': sheet_name,
                                        'row': row_idx + 1,
                                        'column': col,
                                        'canonical_field': canonical_field,
                                        'original': original,
                                        'new': normalized_value,
                                        'confidence': 1.0,
                                        'reason': 'Güvenli numerik dönüşüm'
                                    })
                                else:
                                    suggestions.append({
                                        'sheet': sheet_name,
                                        'row': row_idx + 1,
                                        'column': col,
                                        'canonical_field': canonical_field,
                                        'original': original,
                                        'suggestion': normalized_value,
                                        'confidence': 0.5,
                                        'message': f"Belirsiz format: '{original}'. Önerilen: '{normalized_value}'. Lütfen onaylayın veya düzeltin."
                                    })
                            elif is_ambiguous:
                                suggestions.append({
                                    'sheet': sheet_name,
                                    'row': row_idx + 1,
                                    'column': col,
                                    'canonical_field': canonical_field,
                                    'original': original,
                                    'suggestion': normalized_value,
                                    'confidence': 0.5,
                                    'message': f"Belirsiz format: '{original}'. Lütfen düzeltin."
                                })
                normalized_rows.append(new_row)
            
            normalized[sheet_name] = normalized_rows
            print(f"🔍 {sheet_name} normalize edildi: {len(normalized_rows)} satır")

        # ============================================================
        # Validation hatalarını errors'a ekle
        # ============================================================
        for err in validation_errors:
            # Zaten eklenmiş mi kontrol et
            exists = False
            for existing in errors:
                if (existing.get('sheet') == err.get('sheet') and
                    existing.get('row') == err.get('row') and
                    existing.get('column') == err.get('column')):
                    exists = True
                    break
            if not exists:
                errors.append(err)
        
        # total_errors'i güncelle
        total_errors = len(errors)

        return {
            'normalized_data': normalized,
            'changes': changes,
            'suggestions': suggestions,
            'errors': errors,
            'total_changes': len(changes),
            'total_suggestions': len(suggestions),
            'total_errors': total_errors
        }
    
    def _normalize_numeric(self, value: str) -> Tuple[str, bool, Optional[str]]:
        """
        Numerik bir string'i normalize eder.
        Dönüş: (normalized_value, is_ambiguous, suggestion)
        """
        # Boş veya None kontrolü
        if not value:
            return value, False, None

        # Önce zaten float parse edilebiliyor mu?
        try:
            float(value)
            return value, False, None
        except:
            pass

        # Türkçe format: 1.250,50 -> 1250.50
        match = re.match(r'^(\d{1,3}(?:\.\d{3})*),(\d{2})$', value)
        if match:
            normalized = match.group(1).replace('.', '') + '.' + match.group(2)
            return normalized, False, f"{value} → {normalized}"

        # 125,50 -> 125.50
        match = re.match(r'^(\d+),(\d{2})$', value)
        if match:
            normalized = match.group(1) + '.' + match.group(2)
            return normalized, False, f"{value} → {normalized}"

        # 10.000 -> belirsiz (on bin mi, on virgül sıfır mı?)
        match = re.match(r'^(\d{1,3}\.\d{3})$', value)
        if match:
            # Belirsiz, kullanıcıya bırak
            return value, True, f"'{value}' formatı belirsiz. On bin mi yoksa on virgül sıfır mı?"

        # 10,000 -> belirsiz
        match = re.match(r'^(\d{1,3},\d{3})$', value)
        if match:
            return value, True, f"'{value}' formatı belirsiz. On bin mi yoksa on virgül sıfır mı?"

        # Bilinmeyen format
        return value, True, f"'{value}' formatı tanınmadı. Lütfen düzeltin."


def get_normalization_engine(db: Session, user_id: int, upload_id: str) -> NormalizationEngine:
    return NormalizationEngine(db, user_id, upload_id)