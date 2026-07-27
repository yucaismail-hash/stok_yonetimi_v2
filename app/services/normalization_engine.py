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

# app/services/normalization_engine.py - normalize_data DÜZELTİLDİ

# app/services/normalization_engine.py - normalize_data DÜZELTİLDİ

    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Veriyi normalize et.
        Sadece numerik alanlarda güvenli dönüşüm yapar.
        String alanlara dokunmaz.
        """
        normalized = {}
        changes = []
        suggestions = []
        errors = []

        # Veriyi sheet bazında işle
        for sheet_name, rows in data.items():
            if not rows:
                normalized[sheet_name] = []
                continue

            # ============================================================
            # 1. EĞER ROWS BİR DICT İSE (suppliers veya supplier_mapping gibi)
            # ============================================================
            if isinstance(rows, dict):
                print(f"🔍 {sheet_name} bir dict, dönüştürülüyor...")
                rows_list = []
                if sheet_name == 'suppliers':
                    for key, value in rows.items():
                        if isinstance(value, dict):
                            value['supplier_code'] = key
                            rows_list.append(value)
                        else:
                            rows_list.append(value)
                elif sheet_name == 'supplier_mapping':
                    for product_code, supplier_list in rows.items():
                        if isinstance(supplier_list, list):
                            for item in supplier_list:
                                if isinstance(item, dict):
                                    # ============================================================
                                    # ✅ SADECE GEREKLİ ALANLARI AL
                                    # ============================================================
                                    new_item = {
                                        'supplier_id': item.get('supplier_id', ''),
                                        'share': item.get('share', 1.0),
                                        'open_qty': item.get('open_qty', 0),
                                        'planned_due': item.get('planned_due', ''),
                                    }
                                    rows_list.append(new_item)
                        else:
                            rows_list.append(supplier_list)
                else:
                    for key, value in rows.items():
                        if isinstance(value, dict):
                            value['_key'] = key
                            rows_list.append(value)
                        else:
                            rows_list.append(value)
                
                rows = rows_list
                print(f"🔍 {sheet_name} dönüştürüldü: {len(rows)} satır")

            # ============================================================
            # 2. ROWS BİR LİSTE DEĞİLSE ATLA
            # ============================================================
            if not isinstance(rows, list):
                print(f"⚠️ {sheet_name} rows liste değil: {type(rows)} - atlanıyor")
                normalized[sheet_name] = []
                continue

            # ============================================================
            # 3. HER SATIRI İŞLE
            # ============================================================
            normalized_rows = []
            for row_idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    print(f"⚠️ {sheet_name} - {row_idx}. satır dict değil: {type(row)} - atlanıyor")
                    continue
                
                # ============================================================
                # ✅ SADECE GEREKLİ ALANLARI KORU, FAZLA ALANLARI TEMİZLE
                # ============================================================
                # supplier_mapping için sadece belirli alanları koru
                if sheet_name == 'supplier_mapping':
                    clean_row = {
                        'supplier_id': row.get('supplier_id', ''),
                        'share': row.get('share', 1.0),
                        'open_qty': row.get('open_qty', 0),
                        'planned_due': row.get('planned_due', ''),
                    }
                else:
                    clean_row = dict(row)
                
                new_row = dict(clean_row)
                for col, value in clean_row.items():
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
            print(f"🔍 {sheet_name} normalizasyon tamamlandı: {len(normalized_rows)} satır")

        return {
            'normalized_data': normalized,
            'changes': changes,
            'suggestions': suggestions,
            'errors': errors,
            'total_changes': len(changes),
            'total_suggestions': len(suggestions),
            'total_errors': len(errors)
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