# app/services/validation_engine.py - GÜNCELLENMİŞ (Kolon Eşleştirme Eklendi)

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models import (
    ValidationRule,
    AnalysisImpactRule,
    NormalizationRule,
    ValidationResult
)

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Veri Doğrulama Motoru - 6 adım kontrol
    """
    
    # ✅ ExcelReader anahtarları -> Türkçe sheet adları eşleştirmesi
    SHEET_MAPPING = {
        'materials': 'Temel_Veriler',
        'suppliers': 'Tedarikciler',
        'supplier_mapping': 'Malzeme_Tedarikciler',
    }
    
    # ✅ Kontrol edilecek sheet'ler (Türkçe isimler)
    REQUIRED_SHEETS = ['Temel_Veriler', 'Tedarikciler', 'Malzeme_Tedarikciler']
    
    # ✅ ExcelReader anahtarları
    REQUIRED_KEYS = ['materials', 'suppliers', 'supplier_mapping']
    
    # ✅ KOLON EŞLEŞTİRMESİ: İngilizce -> Türkçe (görünen ad)
    COLUMN_MAPPING = {
        'code': 'Ürün Kodu',
        'description': 'Ürün Adı',
        'group': 'Ürün Grubu',
        'initial_stock': 'Dönem Başı Stok',
        'lead_time_days': 'Tedarik Süresi (Gün)',
        'eoq': 'Sipariş Parti Büyüklüğü',
        'unit_cost': 'Birim Maliyet (TL)',
        'holding_rate': 'Stok Tutma Oranı (%)',
        'shortage_cost': 'Stok Tükenme Maliyeti',
        'historical_demand': 'Talep Geçmişi (W1-Wn)',
        'supplier_id': 'Tedarikçi Kodu',
        'share': 'Tedarik Payı (%)',
        'open_qty': 'Açık Sipariş',
        'planned_due': 'Planlanan Teslim Tarihi',
        'name': 'Tedarikçi Adı',
        'factor': 'Tedarikçi Faktörü',
        'ontime_rate': 'Zamanında Teslim Oranı (%)',
        'lt_mean': 'Ortalama Teslim Süresi (Gün)',
        'lt_std': 'Teslim Süresi Standart Sapması',
    }
    
    # ✅ TERS EŞLEŞTİRME: Türkçe -> İngilizce
    REVERSE_COLUMN_MAPPING = {v: k for k, v in COLUMN_MAPPING.items()}
    
    # ✅ HER SHEET İÇİN GEREKLİ KOLONLAR (Türkçe isimler)
    REQUIRED_COLUMNS = {
        'Temel_Veriler': ['Ürün Kodu', 'Tedarik Süresi (Gün)'],
        'Tedarikciler': ['Tedarikçi Kodu', 'Zamanında Teslim Oranı (%)'],
        'Malzeme_Tedarikciler': ['Ürün Kodu', 'Tedarikçi Kodu', 'Tedarik Payı (%)'],
    }
    
    def __init__(self, db: Session, user_id: int, upload_id: str):
        self.db = db
        self.user_id = user_id
        self.upload_id = upload_id
        self.rules = self._load_rules()
        self.impact_rules = self._load_impact_rules()
    
    def _load_rules(self) -> List[ValidationRule]:
        return self.db.query(ValidationRule).filter(
            ValidationRule.is_active == True
        ).all()
    
    def _load_impact_rules(self) -> List[AnalysisImpactRule]:
        return self.db.query(AnalysisImpactRule).filter(
            AnalysisImpactRule.is_active == True
        ).all()
    
    # ============================================================
    # 📌 YARDIMCI: ExcelReader verisini normalize et
    # ============================================================

    def _normalize_sheets(self, sheets: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        ExcelReader'dan gelen veriyi standart formata çevirir.
        Başlık satırını otomatik filtreler.
        """
        normalized = {}
        
        for key, data in sheets.items():
            # Sheet adını eşleştir
            if key in self.SHEET_MAPPING:
                sheet_name = self.SHEET_MAPPING[key]
            else:
                sheet_name = key.strip()
            
            rows = []
            
            # ✅ ÖZEL DURUM: supplier_mapping (Malzeme_Tedarikciler)
            if key == 'supplier_mapping' and isinstance(data, dict):
                for product_code, supplier_list in data.items():
                    if isinstance(supplier_list, list):
                        for item in supplier_list:
                            if isinstance(item, dict):
                                new_row = {
                                    'Ürün Kodu': product_code,
                                    'Tedarikçi Kodu': item.get('supplier_id', ''),
                                    'Tedarik Payı (%)': item.get('share', 0) * 100,
                                    'Açık Sipariş': item.get('open_qty', 0),
                                    'Planlanan Teslim Tarihi': item.get('planned_due', ''),
                                }
                                rows.append(new_row)
                
                normalized[sheet_name] = rows
                continue
            
            # ✅ ÖZEL DURUM: suppliers (Tedarikciler)
            if key == 'suppliers' and isinstance(data, dict):
                for supplier_code, supplier_data in data.items():
                    if isinstance(supplier_data, dict):
                        new_row = {
                            'Tedarikçi Kodu': supplier_code,
                            'Tedarikçi Adı': supplier_data.get('name', ''),
                            'Tedarikçi Faktörü': supplier_data.get('factor', 1.0),
                            'Zamanında Teslim Oranı (%)': supplier_data.get('ontime_rate', 0) * 100,
                            'Ortalama Teslim Süresi (Gün)': supplier_data.get('lt_mean', ''),
                            'Teslim Süresi Standart Sapması': supplier_data.get('lt_std', ''),
                        }
                        rows.append(new_row)
                
                normalized[sheet_name] = rows
                continue
            
            # ✅ NORMAL DURUM: materials (Temel_Veriler) - Başlık satırını filtrele
            if key == 'materials' and isinstance(data, list):
                print(f"🔍 materials: {len(data)} satır (ham)")
                
                clean_rows = []
                skip_count = 0
                
                # İlk satırı kontrol et - başlık mı?
                if data and isinstance(data[0], dict):
                    first_row = data[0]
                    first_row_keys = list(first_row.keys())
                    
                    # Başlık satırı tespiti:
                    # 1. 'code' anahtarı yoksa
                    # 2. 'code' değeri 'Ürün Kodu' veya 'code' ise
                    # 3. 'code' değeri boş veya None ise
                    is_header_row = (
                        'code' not in first_row_keys or
                        first_row.get('code') == 'Ürün Kodu' or
                        first_row.get('code') == 'code' or
                        first_row.get('code') == '' or
                        first_row.get('code') is None
                    )
                    
                    if is_header_row:
                        skip_count += 1
                        print(f"⚠️ Başlık satırı atlandı (keys: {first_row_keys})")
                        data = data[1:]  # İlk satırı atla
                
                # Kalan satırları işle
                for row in data:
                    if isinstance(row, dict):
                        code = row.get('code', '')
                        
                        # Boş veya geçersiz satır mı?
                        if code is None or code == '' or code == 0 or code == '0':
                            print(f"⚠️ Boş satır atlandı (code: {code})")
                            continue
                        
                        # Kolon isimlerini Türkçe'ye çevir
                        new_row = {}
                        for col_key, value in row.items():
                            turkish_key = self.COLUMN_MAPPING.get(col_key, col_key)
                            new_row[turkish_key] = value
                        clean_rows.append(new_row)
                
                normalized[sheet_name] = clean_rows
                print(f"🔍 Temel_Veriler: {len(clean_rows)} satır ({skip_count} başlık filtrelendi)")
                continue
            
            # ✅ DİĞER SHEET'LER için genel işlem
            if isinstance(data, dict):
                if 'data' in data and isinstance(data['data'], list):
                    rows = data['data']
                elif 'rows' in data and isinstance(data['rows'], list):
                    rows = data['rows']
                else:
                    for k, v in data.items():
                        if isinstance(v, list) and v:
                            rows = v
                            break
                        elif isinstance(v, dict) and v:
                            rows = [v]
                            break
            elif isinstance(data, list):
                rows = data
            
            # Kolon isimlerini Türkçe'ye çevir
            clean_rows = []
            for row in rows:
                if isinstance(row, dict):
                    new_row = {}
                    for col_key, value in row.items():
                        turkish_key = self.COLUMN_MAPPING.get(col_key, col_key)
                        new_row[turkish_key] = value
                    clean_rows.append(new_row)
            
            normalized[sheet_name] = clean_rows
        
        # DEBUG
        print(f"🔍 Normalize edilmiş sheets: {list(normalized.keys())}")
        for name, rows in normalized.items():
            print(f"   📄 {name}: {len(rows)} satır")
            if rows:
                print(f"      ilk satır: {list(rows[0].keys()) if isinstance(rows[0], dict) else 'dict değil'}")
        
        return normalized

    # ============================================================
    # STEP 1: Excel Dosyası Bilgileri
    # ============================================================
    
    def get_file_info(self, file_name: str, file_size: int, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """Dosya bilgilerini topla"""
        normalized = self._normalize_sheets(sheets)
        
        total_rows = 0
        total_cols = 0
        
        for sheet_name, rows in normalized.items():
            total_rows += len(rows)
            if rows and isinstance(rows[0], dict):
                total_cols = max(total_cols, len(rows[0]))
        
        return {
            'file_name': file_name,
            'file_size': file_size,
            'sheet_count': len(normalized),
            'total_rows': total_rows,
            'total_cols': total_cols,
            'sheets': list(normalized.keys())
        }
    
    # ============================================================
    # STEP 2: Sheet Kontrolü
    # ============================================================
    
    def check_sheets(self, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """Gerekli sheet'lerin varlığını kontrol et"""
        normalized = self._normalize_sheets(sheets)
        sheet_names = list(normalized.keys())
        
        print(f"🔍 Sheet kontrolü - Mevcut sheet'ler: {sheet_names}")
        print(f"🔍 Aranan sheet'ler: {self.REQUIRED_SHEETS}")
        
        results = []
        missing = []
        found = []
        
        for required in self.REQUIRED_SHEETS:
            exists = False
            
            if required in sheet_names:
                exists = True
            else:
                for name in sheet_names:
                    if name.lower() == required.lower():
                        exists = True
                        break
                if not exists:
                    for name in sheet_names:
                        if required.lower() in name.lower() or name.lower() in required.lower():
                            exists = True
                            break
            
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
        
        return {
            'success': len(missing) == 0,
            'found': found,
            'missing': missing,
            'results': results,
            'summary': f"{len(found)}/{len(self.REQUIRED_SHEETS)} sheet bulundu."
        }
    
    # ============================================================
    # STEP 3: Veri Kalitesi Kontrolü
    # ============================================================
    
    def validate_data_quality(self, sheets: Dict[str, Any]) -> Dict[str, Any]:
        """Veri kalitesi kontrolü - KRİTİK ALANLAR SATIR BAZLI KONTROL"""
        results = {
            'column_checks': [],
            'structural_checks': [],
            'missing_data': [],
            'data_type_errors': [],
            'business_rule_errors': [],
            'summary': {},
            'score': 100,
            'can_proceed': True,
        }
        
        normalized = self._normalize_sheets(sheets)
        
        if not normalized:
            results['can_proceed'] = False
            results['summary'] = {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'score': 0,
                'error': 'Hiç veri bulunamadı!'
            }
            results['score'] = 0
            return results
        
        # Sheet kontrolü
        sheet_names = list(normalized.keys())
        for required in self.REQUIRED_SHEETS:
            if required not in sheet_names:
                results['can_proceed'] = False
                results['structural_checks'].append({
                    'sheet': required,
                    'status': 'error',
                    'message': f"'{required}' sheet'i bulunamadı.",
                    'type': 'structural'
                })
        
        # 📌 TEMEL_VERILER için özel kontrol
        temel_veriler = normalized.get('Temel_Veriler', [])
        print(f"🔍 Toplam {len(temel_veriler)} satır kontrol ediliyor...")
        empty_count = 0
        for idx, row in enumerate(temel_veriler):
            if isinstance(row, dict):
                code = row.get('Ürün Kodu', '')
                if code is None or code == '' or code == 0 or (isinstance(code, str) and code.strip() == ''):
                    empty_count += 1
                    print(f"❌ {idx+1}. satırda Ürün Kodu BOŞ! (Diğer alanlar: {list(row.keys())})")
                    results['missing_data'].append({
                        'sheet': 'Temel_Veriler',
                        'row': idx + 1,
                        'column': 'Ürün Kodu',
                        'value': code,
                        'severity': 'error',
                        'message': f"Ürün Kodu {idx+1}. satırda BOŞ!",
                        'recommendation': 'Ürün Kodu alanını doldurun.'
                    })
                    results['can_proceed'] = False
        
        print(f"🔍 Toplam {empty_count} satırda Ürün Kodu boş!")

        critical_columns = ['Ürün Kodu', 'Tedarik Süresi (Gün)']
        missing_critical_rows = 0
        
        for sheet_name, rows in normalized.items():
            if not rows:
                results['structural_checks'].append({
                    'sheet': sheet_name,
                    'status': 'error',
                    'message': f"'{sheet_name}' sheet'i tamamen boş.",
                    'type': 'structural'
                })
                results['can_proceed'] = False
                continue
            
            columns = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
            required_columns = self.REQUIRED_COLUMNS.get(sheet_name, [])
            
            # Kolon kontrolü
            for col in required_columns:
                exists = col in columns
                results['column_checks'].append({
                    'sheet': sheet_name,
                    'column': col,
                    'exists': exists,
                    'status': 'success' if exists else 'error',
                    'message': f"{col} kolonu mevcut." if exists else f"{col} kolonu bulunamadı."
                })
                
                if not exists and col in critical_columns:
                    results['can_proceed'] = False
            
            # 📌 SATIR BAZLI KRİTİK ALAN KONTROLÜ
            for idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                
                # Kritik alanlar: Ürün Kodu ve Tedarik Süresi (Gün)
                for col in critical_columns:
                    if col in row:
                        value = row.get(col)
                        # Boş mu kontrol et (None, '', 0, '0')
                        is_empty = (
                            value is None or 
                            value == '' or 
                            value == 0 or 
                            value == '0' or
                            (isinstance(value, str) and value.strip() == '')
                        )
                        if is_empty:
                            missing_critical_rows += 1
                            results['missing_data'].append({
                                'sheet': sheet_name,
                                'row': idx + 1,
                                'column': col,
                                'value': value,
                                'severity': 'error',
                                'message': f"{col} alanı {idx+1}. satırda boş!",
                                'recommendation': f"{col} alanını doldurun."
                            })
                            results['can_proceed'] = False
                            results['score'] = max(0, results['score'] - 10)  # Her hata -10 puan
                
                # Diğer alanlar için uyarı
                for col in required_columns:
                    if col not in critical_columns and col in row:
                        value = row.get(col)
                        if value is None or value == '':
                            results['missing_data'].append({
                                'sheet': sheet_name,
                                'row': idx + 1,
                                'column': col,
                                'value': value,
                                'severity': 'warning',
                                'message': f"{col} alanı {idx+1}. satırda boş.",
                                'recommendation': f"{col} alanını doldurmanız önerilir."
                            })
                            results['score'] = max(0, results['score'] - 2)
            
            # ✅ Business Rule Kontrolleri
            for idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                
                # Negatif stok kontrolü
                if 'Dönem Başı Stok' in row:
                    value = row.get('Dönem Başı Stok')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Dönem Başı Stok',
                                    'value': value,
                                    'rule': 'negative_stock',
                                    'severity': 'error',
                                    'message': f"{idx+1}. satırda Dönem Başı Stok negatif: {value}",
                                    'recommendation': 'Stok miktarı negatif olamaz. Lütfen düzeltin.'
                                })
                        except ValueError:
                            pass
                
                # Negatif maliyet kontrolü
                if 'Birim Maliyet (TL)' in row:
                    value = row.get('Birim Maliyet (TL)')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Birim Maliyet (TL)',
                                    'value': value,
                                    'rule': 'negative_cost',
                                    'severity': 'error',
                                    'message': f"{idx+1}. satırda Birim Maliyet negatif: {value}",
                                    'recommendation': 'Birim maliyet negatif olamaz. Lütfen düzeltin.'
                                })
                        except ValueError:
                            pass
                
                # Negatif tedarik süresi
                if 'Tedarik Süresi (Gün)' in row:
                    value = row.get('Tedarik Süresi (Gün)')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Tedarik Süresi (Gün)',
                                    'value': value,
                                    'rule': 'negative_lead_time',
                                    'severity': 'error',
                                    'message': f"{idx+1}. satırda Tedarik Süresi negatif: {value}",
                                    'recommendation': 'Tedarik süresi negatif olamaz. Lütfen düzeltin.'
                                })
                        except ValueError:
                            pass
                
                # Holding Rate sınırları (0-100)
                if 'Stok Tutma Oranı (%)' in row:
                    value = row.get('Stok Tutma Oranı (%)')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0 or num_value > 100:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Stok Tutma Oranı (%)',
                                    'value': value,
                                    'rule': 'holding_rate_out_of_range',
                                    'severity': 'warning',
                                    'message': f"{idx+1}. satırda Stok Tutma Oranı %{value} (0-100 arası olmalı)",
                                    'recommendation': 'Stok tutma oranı 0-100 arasında olmalıdır.'
                                })
                        except ValueError:
                            pass
                
                # Tedarik Payı sınırları (0-100)
                if 'Tedarik Payı (%)' in row:
                    value = row.get('Tedarik Payı (%)')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0 or num_value > 100:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Tedarik Payı (%)',
                                    'value': value,
                                    'rule': 'supplier_share_out_of_range',
                                    'severity': 'warning',
                                    'message': f"{idx+1}. satırda Tedarik Payı %{value} (0-100 arası olmalı)",
                                    'recommendation': 'Tedarik payı 0-100 arasında olmalıdır.'
                                })
                        except ValueError:
                            pass
                
                # Zamanında Teslim Oranı sınırları (0-100)
                if 'Zamanında Teslim Oranı (%)' in row:
                    value = row.get('Zamanında Teslim Oranı (%)')
                    if value is not None and value != '':
                        try:
                            num_value = float(value)
                            if num_value < 0 or num_value > 100:
                                results['business_rule_errors'].append({
                                    'sheet': sheet_name,
                                    'row': idx + 1,
                                    'column': 'Zamanında Teslim Oranı (%)',
                                    'value': value,
                                    'rule': 'ontime_rate_out_of_range',
                                    'severity': 'warning',
                                    'message': f"{idx+1}. satırda Zamanında Teslim Oranı %{value} (0-100 arası olmalı)",
                                    'recommendation': 'Zamanında teslim oranı 0-100 arasında olmalıdır.'
                                })
                        except ValueError:
                            pass
        
        # Score hesapla
        total_checks = len(results['column_checks'])
        failed_checks = sum(1 for c in results['column_checks'] if c['status'] == 'error')
        missing_errors = len([m for m in results['missing_data'] if m.get('severity') == 'error'])
        missing_warnings = len([m for m in results['missing_data'] if m.get('severity') == 'warning'])
        
        # Eğer kritik alanlarda eksik varsa skor ciddi düşer
        if missing_critical_rows > 0:
            # Her kritik satır hatası -15 puan, max 100
            penalty = min(90, missing_critical_rows * 15)
            results['score'] = max(0, 100 - penalty)
        
        # Eğer kolon eksik varsa skor düşer
        if total_checks > 0:
            column_penalty = (failed_checks / total_checks * 100) * 0.5
            results['score'] = max(0, results['score'] - column_penalty)
        
        # Eğer uyarı varsa skor hafif düşer
        results['score'] = max(0, results['score'] - (missing_warnings * 2))
        
        results['summary'] = {
            'total_checks': total_checks,
            'passed': total_checks - failed_checks,
            'failed': failed_checks,
            'business_errors': len(results['business_rule_errors']),
            'missing_errors': missing_errors,
            'missing_warnings': missing_warnings,
            'missing_critical_rows': missing_critical_rows,
            'score': round(results['score'], 1)
        }
        
        return results

    def _get_columns(self, data: Any) -> List[str]:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return list(data[0].keys())
        return []
    
    def _get_required_columns(self, sheet_name: str) -> List[str]:
        return self.REQUIRED_COLUMNS.get(sheet_name, [])
    
    # ============================================================
    # STEP 4: Smart Data Normalization
    # ============================================================
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Akıllı veri standardizasyonu"""
        rules = self.db.query(NormalizationRule).filter(
            NormalizationRule.is_active == True
        ).all()
        
        normalized = self._normalize_sheets(data)
        changes = []
        
        for sheet_name, rows in normalized.items():
            if not rows:
                continue
            
            for row_idx, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                
                new_row = dict(row)
                for key, value in row.items():
                    if isinstance(value, str):
                        original = value
                        new_value = self._apply_normalization(value, rules)
                        if new_value != original:
                            changes.append({
                                'sheet': sheet_name,
                                'column': key,
                                'original': original,
                                'new': new_value,
                                'confidence': 0.95
                            })
                        new_row[key] = new_value
                rows[row_idx] = new_row
        
        return {
            'normalized_data': normalized,
            'changes': changes,
            'total_changes': len(changes)
        }

    def _apply_normalization(self, value: str, rules: List[NormalizationRule]) -> str:
        """
        Sadece sayısal format düzeltmeleri ve boşluk/tab temizliği yapar.
        String alanlara (Ürün Grubu, Tedarikçi Adı vb.) müdahale etmez.
        """
        result = value
        
        # ✅ 1. Baş ve sondaki boşlukları temizle (HER ZAMAN)
        result = result.strip()
        
        # ✅ 2. TAB karakterlerini temizle (HER ZAMAN)
        result = result.replace('\t', ' ')
        
        # ✅ 3. Çoklu boşlukları tek boşluğa çevir (HER ZAMAN)
        result = re.sub(r'\s+', ' ', result)
        
        # ✅ 4. SADECE SAYISAL FORMAT DÜZELTMELERİ
        # Tespit: Değer sayısal bir ifade mi?
        is_numeric = False
        
        # 4a. 10.000 → 10000 (nokta binlik ayraç)
        if re.match(r'^[\d,.]{1,}([\.,][\d]{3}){1,}$', result):
            is_numeric = True
            original = result
            result = result.replace('.', '').replace(',', '')
            # Eğer sonunda .00 varsa temizle (10.000.00 → 10000)
            if result.endswith('.00'):
                result = result[:-3]
            print(f"🔧 Sayısal düzeltme: {original} → {result}")
        
        # 4b. 10000,00 → 10000.00 (virgül ondalık ayraç)
        elif re.match(r'^\d+,\d{2}$', result):
            is_numeric = True
            original = result
            result = result.replace(',', '.')
            print(f"🔧 Sayısal düzeltme: {original} → {result}")
        
        # 4c. 10,000.00 → 10000.00
        elif re.match(r'^\d{1,3}(,\d{3})*(\.\d{2})?$', result):
            is_numeric = True
            original = result
            result = result.replace(',', '')
            print(f"🔧 Sayısal düzeltme: {original} → {result}")
        
        # 4d. Yüzde değerleri: 0.9 → 90 (eğer yüzde kolonu ise)
        # Bu kontroller column bazında yapılamıyor, bu yüzden atlıyoruz
        
        # ✅ 5. BÜYÜK HARFE ÇEVİRMEYİ KALDIR
        # Sadece Ürün Kodu gibi özel alanlar için yapılabilir, ama şimdilik kaldır
        
        return result
    
    # ============================================================
    # STEP 5: Analysis Impact Assessment
    # ============================================================
     
    def analyze_impact(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analysis Impact Assessment Engine
        Her eksiklik için: Sorun → Sebep → Etkilenen Analizler → Beklenen Sonuç → Öneri
        """
        normalized = self._normalize_sheets(data)
        
        results = {}
        analysis_scores = {}
        detailed_impacts = []  # ✅ Detaylı impact listesi
        
        analyses = ['forecast', 'safety_stock', 'supplier', 'simulation', 'backtest']
        
        # Her analiz için etki hesapla
        for analysis in analyses:
            impact, score = self._analyze_single_impact(analysis, normalized)
            results[analysis] = impact
            analysis_scores[analysis] = score
            
            # ✅ Detaylı impact oluştur
            for item in impact:
                if item['status'] == 'missing':
                    detailed_impacts.append({
                        'analysis': analysis,
                        'field': item['field'],
                        'importance': item['importance'],
                        'problem': item['message'],
                        'reason': self._get_impact_reason(analysis, item['field']),
                        'affected_analyses': self._get_affected_analyses(analysis, item['field']),
                        'expected_result': self._get_expected_result(analysis, item['field']),
                        'recommendation': item.get('recommendation', 'Veriyi doldurun.')
                    })
        
        ai_comment = self._generate_impact_comment(results, analysis_scores)
        ai_recommendation = self._generate_ai_recommendation(results, analysis_scores, detailed_impacts)
        
        return {
            'analysis_scores': analysis_scores,
            'analysis_results': results,
            'detailed_impacts': detailed_impacts,  # ✅ YENİ
            'ai_comment': ai_comment,
            'ai_recommendation': ai_recommendation,  # ✅ YENİ
            'overall_score': sum(analysis_scores.values()) / len(analysis_scores) if analysis_scores else 0
        }

    def _get_impact_reason(self, analysis: str, field: str) -> str:
        """Eksiklik için sebep üret"""
        reasons = {
            'forecast': {
                'Ürün Kodu': 'Forecast için ürün bazlı tahmin yapılması gerekir.',
                'W1-Wn': 'Talep geçmişi olmadan tahmin üretilemez.',
                'Ürün Grubu': 'AI öğrenmesi grup bazında yapılır.',
            },
            'safety_stock': {
                'Ürün Kodu': 'Emniyet stoğu ürün bazında hesaplanır.',
                'W1-Wn': 'Talep değişkenliği hesaplanamaz.',
                'Tedarik Süresi (Gün)': 'Teslimat süresi olmadan SS hesaplanamaz.',
            },
            'supplier': {
                'Tedarikçi Kodu': 'Tedarikçi tanımlanmamış.',
                'Zamanında Teslim Oranı (%)': 'Tedarikçi performansı değerlendirilemez.',
            },
            'simulation': {
                'Ürün Kodu': 'Simülasyon ürün bazında çalışır.',
                'W1-Wn': 'Talep dağılımı olmadan simülasyon yapılamaz.',
                'Tedarik Süresi (Gün)': 'Teslimat süresi simülasyonda kritiktir.',
            },
            'backtest': {
                'Ürün Kodu': 'Backtest ürün bazında yapılır.',
                'W1-Wn': 'Geçmiş veri olmadan backtest yapılamaz.',
            }
        }
        return reasons.get(analysis, {}).get(field, 'Veri eksikliği analizi etkiler.')

    def _get_affected_analyses(self, analysis: str, field: str) -> List[str]:
        """Hangi analizler etkilenir"""
        affected = [analysis]
        # Ek analizleri belirle
        if field == 'Ürün Kodu':
            affected = ['forecast', 'safety_stock', 'simulation', 'backtest']
        elif field == 'W1-Wn':
            affected = ['forecast', 'safety_stock', 'simulation', 'backtest']
        elif field == 'Tedarik Süresi (Gün)':
            affected = ['safety_stock', 'simulation']
        elif field == 'Tedarikçi Kodu':
            affected = ['supplier']
        return list(set(affected))

    def _get_expected_result(self, analysis: str, field: str) -> str:
        """Beklenen sonuç"""
        results = {
            'forecast': 'Tahmin doğruluğu azalabilir veya tahmin yapılamayabilir.',
            'safety_stock': 'Emniyet stoğu hesaplanamayabilir veya hatalı olabilir.',
            'supplier': 'Tedarikçi analizi yapılamayabilir.',
            'simulation': 'Simülasyon sonuçları güvenilir olmayabilir.',
            'backtest': 'Backtest sonuçları hatalı olabilir.',
        }
        return results.get(analysis, 'Analiz doğruluğu etkilenir.')

    def _generate_ai_recommendation(self, results: Dict, scores: Dict, detailed_impacts: List) -> str:
        """AI Önerisi oluştur"""
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        critical_issues = [i for i in detailed_impacts if i['importance'] == 'Kritik']
        
        if avg_score >= 90 and not critical_issues:
            return "✅ Veri seti mükemmel durumda. Tüm analizler başarıyla çalıştırılabilir."
        elif avg_score >= 70 and len(critical_issues) <= 2:
            return f"⚠️ Veri seti iyi durumda. {len(critical_issues)} kritik eksiklik var. Düzeltilmesi önerilir."
        elif avg_score >= 50:
            return f"⚠️ Veri setinde {len(critical_issues)} kritik eksiklik var. Analiz doğruluğu etkilenebilir."
        else:
            return "❌ Veri seti yetersiz. Kritik alanlar eksik. Lütfen verileri düzenleyin."

    def _analyze_single_impact(self, analysis: str, data: Dict[str, Any]) -> Tuple[List[Dict], float]:
        impacts = []
        score = 100
        
        required_fields = self.db.query(AnalysisImpactRule).filter(
            AnalysisImpactRule.analysis_type == analysis,
            AnalysisImpactRule.is_active == True
        ).all()
        
        if not required_fields:
            return impacts, score
        
        for field in required_fields:
            exists = self._check_field_exists(field.field_name, data)
            
            if not exists and field.importance == 'critical':
                score -= 20
                impacts.append({
                    'field': field.field_name,
                    'importance': 'Kritik',
                    'status': 'missing',
                    'message': f"{field.field_name} alanı eksik. {analysis} analizi çalışmayabilir.",
                    'recommendation': f"{field.field_name} alanını doldurun."
                })
            elif not exists and field.importance == 'recommended':
                score -= 10
                impacts.append({
                    'field': field.field_name,
                    'importance': 'Önerilen',
                    'status': 'missing',
                    'message': f"{field.field_name} alanı eksik. {analysis} analizi doğruluğu etkilenebilir.",
                    'recommendation': f"{field.field_name} alanını doldurmanız önerilir."
                })
            elif not exists and field.importance == 'optional':
                impacts.append({
                    'field': field.field_name,
                    'importance': 'Opsiyonel',
                    'status': 'optional',
                    'message': f"{field.field_name} alanı opsiyonel.",
                    'recommendation': None
                })
            else:
                impacts.append({
                    'field': field.field_name,
                    'importance': field.importance,
                    'status': 'ok',
                    'message': f"{field.field_name} alanı mevcut.",
                    'recommendation': None
                })
        
        return impacts, max(0, score)
    
    def _check_field_exists(self, field_name: str, data: Dict[str, Any]) -> bool:
        for sheet_name, rows in data.items():
            if not rows:
                continue
            if rows and isinstance(rows[0], dict):
                if field_name in rows[0]:
                    return True
        return False
    
    def _generate_impact_comment(self, results: Dict, scores: Dict) -> str:
        avg_score = sum(scores.values()) / len(scores) if scores else 0
        
        if avg_score >= 90:
            return "Dataset analiz için uygundur. Tüm analizler başarıyla çalıştırılabilir."
        elif avg_score >= 70:
            return "Dataset analiz için kısmen uygundur. Bazı analizlerde doğruluk kaybı yaşanabilir."
        elif avg_score >= 50:
            return "Dataset analiz için sınırlı uygundur. Eksik alanlar tamamlanmalıdır."
        else:
            return "Dataset analiz için uygun değildir. Kritik alanlar eksiktir. Lütfen verileri düzenleyin."
    
    # ============================================================
    # STEP 6: Son Onay Ekranı
    # ============================================================
    
    def get_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'step1_file_info': all_results.get('file_info', {}),
            'step2_sheet_check': all_results.get('sheet_check', {}),
            'step3_data_quality': all_results.get('data_quality', {}),
            'step4_normalization': all_results.get('normalization', {}),
            'step5_impact': all_results.get('impact', {}),
            'summary': self._generate_final_summary(all_results)
        }
    
    def _generate_final_summary(self, results: Dict) -> str:
        parts = []
        
        sheet_check = results.get('sheet_check', {})
        if sheet_check.get('success'):
            parts.append("✅ Tüm gerekli sheet'ler mevcut.")
        else:
            missing = sheet_check.get('missing', [])
            parts.append(f"⚠️ Eksik sheet'ler: {', '.join(missing)}")
        
        quality = results.get('data_quality', {})
        quality_score = quality.get('summary', {}).get('score', 0)
        if quality_score >= 80:
            parts.append(f"✅ Veri kalitesi: %{quality_score:.0f}")
        elif quality_score >= 60:
            parts.append(f"⚠️ Veri kalitesi: %{quality_score:.0f} (iyileştirme önerilir)")
        else:
            parts.append(f"❌ Veri kalitesi: %{quality_score:.0f} (düzeltme gerekli)")
        
        norm = results.get('normalization', {})
        if norm.get('total_changes', 0) > 0:
            parts.append(f"🔄 {norm['total_changes']} otomatik düzeltme yapıldı.")
        
        impact = results.get('impact', {})
        if impact:
            scores = impact.get('analysis_scores', {})
            if scores:
                avg = sum(scores.values()) / len(scores)
                parts.append(f"📊 Analiz hazırlık skoru: %{avg:.0f}")
        
        return " | ".join(parts)


def get_validation_engine(db: Session, user_id: int, upload_id: str) -> ValidationEngine:
    return ValidationEngine(db, user_id, upload_id)