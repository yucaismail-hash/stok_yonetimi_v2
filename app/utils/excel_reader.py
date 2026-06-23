import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re

class ExcelReader:
    """Excel dosyasından veri okuma ve işleme (Çalışma Prensibi v1 uyumlu)"""
    
    def __init__(self):
        self.required_columns = [
            'Malzeme_Kodu', 'Mal_Grubu', 'Termin_Suresi', 'Tedarik_Parti_Büyüklügü'
        ]
        self.min_weeks = 12
        self.max_weeks = 156  # 3 yıl
        
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Excel dosyasını oku ve tüm sheet'leri işle
        Dönüş: {'success': bool, 'data': {...}, 'errors': [...], 'warnings': [...], 'summary': {...}}
        """
        try:
            sheets = pd.read_excel(file_path, sheet_name=None, header=0)
            
            result = {
                'success': False,
                'data': {},
                'errors': [],
                'warnings': [],
                'summary': {}
            }
            
            # 1. Temel_Veriler sheet kontrolü
            if 'Temel_Veriler' not in sheets:
                result['errors'].append("❌ 'Temel_Veriler' sheet'i bulunamadı!")
                return result
            
            df_main = sheets['Temel_Veriler']
            
            # 2. Zorunlu sütun kontrolü
            missing_cols = [col for col in self.required_columns if col not in df_main.columns]
            if missing_cols:
                result['errors'].append(f"❌ Eksik sütunlar: {', '.join(missing_cols)}")
                return result
            
            # 3. W sütunlarını tespit et
            week_cols = self._find_week_columns(df_main.columns)
            if len(week_cols) < self.min_weeks:
                result['errors'].append(
                    f"❌ Yetersiz W sütunu: {len(week_cols)} hafta (en az {self.min_weeks} gerekli)"
                )
                return result
            if len(week_cols) > self.max_weeks:
                result['warnings'].append(
                    f"⚠️ {len(week_cols)} hafta veri var, ilk {self.max_weeks} hafta kullanılacak."
                )
                week_cols = week_cols[:self.max_weeks]
            
            # 4. Her malzeme satırını işle
            materials = []
            error_rows = []
            warning_rows = []
            
            for idx, row in df_main.iterrows():
                try:
                    material = self._process_material_row(row, idx, week_cols)
                    if material:
                        materials.append(material)
                    else:
                        error_rows.append(idx+2)  # Excel satır numarası
                except Exception as e:
                    error_rows.append(idx+2)
                    result['errors'].append(f"Satır {idx+2}: {str(e)}")
            
            if not materials:
                result['errors'].append("❌ Hiç geçerli malzeme bulunamadı!")
                return result
            
            # 5. Uyarılar: Mal_Grubu boş olanlar
            empty_group = [m['code'] for m in materials if not m['group'] or m['group'] == 'GENEL']
            if empty_group:
                result['warnings'].append(
                    f"⚠️ {len(empty_group)} malzemenin Mal_Grubu boş, 'GENEL' olarak atandı: {', '.join(empty_group[:5])}"
                )
            
            # 6. Tedarikçi sheet'leri
            result['data']['materials'] = materials
            result['data']['week_columns'] = week_cols
            
            # Malzeme_Tedarikciler
            if 'Malzeme_Tedarikciler' in sheets:
                supplier_mapping = self._process_supplier_mapping(sheets['Malzeme_Tedarikciler'])
                result['data']['supplier_mapping'] = supplier_mapping
                # Kontrol: mapping'de olmayan malzemeler var mı?
                mapped_codes = set(supplier_mapping.keys())
                material_codes = set(m['code'] for m in materials)
                unmapped = material_codes - mapped_codes
                if unmapped:
                    result['warnings'].append(
                        f"⚠️ {len(unmapped)} malzeme için tedarikçi eşleştirmesi yok: {', '.join(list(unmapped)[:5])}"
                    )
            else:
                result['warnings'].append("ℹ️ 'Malzeme_Tedarikciler' sheet'i bulunamadı. Tek tedarikçi varsayılacak.")
                result['data']['supplier_mapping'] = {}
            
            # Tedarikciler
            if 'Tedarikciler' in sheets:
                suppliers = self._process_suppliers(sheets['Tedarikciler'])
                result['data']['suppliers'] = suppliers
                if not suppliers:
                    result['warnings'].append("⚠️ 'Tedarikciler' sheet'i boş, varsayılan tedarikçi bilgileri kullanılacak.")
            else:
                result['warnings'].append("ℹ️ 'Tedarikciler' sheet'i bulunamadı. Varsayılan tedarikçi bilgileri kullanılacak.")
                result['data']['suppliers'] = {}
            
            # 7. Özet
            result['summary'] = {
                'total_materials': len(materials),
                'total_weeks': len(week_cols),
                'error_rows': error_rows,
                'warning_rows': warning_rows,
                'has_suppliers': bool(result['data']['suppliers']),
                'has_mapping': bool(result['data']['supplier_mapping'])
            }
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'success': False,
                'data': {},
                'errors': [f"❌ Excel okuma hatası: {str(e)}"],
                'warnings': [],
                'summary': {}
            }
    
    def _find_week_columns(self, columns: List[str]) -> List[str]:
        """W sütunlarını bul ve sırala"""
        week_cols = []
        for col in columns:
            col_str = str(col).strip().upper()
            if col_str.startswith('W') and len(col_str) > 1:
                num_part = col_str[1:]
                if num_part.isdigit():
                    week_cols.append(col)
        week_cols.sort(key=lambda x: int(str(x).upper()[1:]))
        return week_cols
    
    def _process_material_row(self, row: pd.Series, idx: int, week_cols: List[str]) -> Dict:
        """Tek bir malzeme satırını işle"""
        material_code = str(row.get('Malzeme_Kodu', '')).strip()
        if not material_code or pd.isna(material_code):
            return None
        
        # 📌 HAFTA VERİLERİNİ DOĞRUDAN OKU
        demand = []
        for week_col in week_cols:
            val = row.get(week_col)
            # ✅ Doğrudan float değerini al
            demand.append(self._safe_float(val))
        
        # 📌 DEBUG: Kontrol et
        print(f"🔍 {material_code} W verileri: {demand[:12]}")
        
        # En az 12 hafta kontrolü
        if len(demand) < self.min_weeks:
            print(f"⚠️ {material_code}: {len(demand)} hafta veri var, en az {self.min_weeks} gerekli")
            return None
        
        # 📌 Sıfır kontrolü - Tüm değerler sıfırsa uyarı ver
        if all(d == 0 for d in demand[:self.min_weeks]):
            print(f"⚠️ {material_code}: Tüm W değerleri sıfır!")
            # Yine de devam et, pattern SIFIR_TALEP olacak
        
        # Malzeme objesi
        material = {
            'code': material_code,
            'description': str(row.get('Malzeme_Aciklama', material_code)),
            'group': str(row.get('Mal_Grubu', 'GENEL')) or 'GENEL',
            'initial_stock': self._safe_float(row.get('Donem_Basi_Stok', 0)),
            'lead_time_days': int(self._safe_float(row.get('Termin_Suresi', 14))),
            'eoq': int(self._safe_float(row.get('Tedarik_Parti_Büyüklügü', 100))),
            'unit_cost': self._safe_float(row.get('Birim_Maliyet', 100)),
            'holding_rate': self._safe_float(row.get('Stok_Tutma_Oranı', 0.2)),
            'shortage_cost': self._safe_float(row.get('Stok_Tukenme_Maliyeti', 500)),
            'historical_demand': demand[:self.max_weeks]
        }
        return material

    def _process_supplier_mapping(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Malzeme-Tedarikçi eşleştirmeleri"""
        mapping = {}
        for _, row in df.iterrows():
            material_code = str(row.get('Malzeme_Kodu', '')).strip()
            supplier_id = str(row.get('Tedarikci_Kodu', '')).strip()
            if not material_code or not supplier_id:
                continue
            if material_code not in mapping:
                mapping[material_code] = []
            mapping[material_code].append({
                'supplier_id': supplier_id,
                'share': self._safe_float(row.get('Pay', 1.0)),
                'open_qty': self._safe_float(row.get('Acik_Bakiye', 0)),
                'planned_due': row.get('Planli_Termin', None) if not pd.isna(row.get('Planli_Termin')) else None
            })
        return mapping
    
    def _process_suppliers(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Tedarikçi bilgileri"""
        suppliers = {}
        for _, row in df.iterrows():
            supplier_id = str(row.get('Tedarikci_Kodu', '')).strip()
            if not supplier_id:
                continue
            suppliers[supplier_id] = {
                'name': str(row.get('Tedarikci_Adi', supplier_id)),
                'factor': self._safe_float(row.get('Supplier_Factor', 1.0)),
                'ontime_rate': self._safe_float(row.get('OnTimeRate', 0.8)),
                'lt_mean': self._safe_float(row.get('LT_Ortalama_Gun', 14)),
                'lt_std': self._safe_float(row.get('LT_Std_Gun', 3))
            }
        return suppliers
    
    def _safe_float(self, value) -> float:
        """Güvenli float dönüşümü - Virgüllü sayıları düzgün işle"""
        try:
            if pd.isna(value) or value is None:
                return 0.0
            if isinstance(value, (int, float)):
                # NaN ve Inf kontrolü
                if np.isnan(value) or np.isinf(value):
                    return 0.0
                return float(value)
            if isinstance(value, str):
                value = str(value).strip()
                # ✅ Virgülü noktaya çevir (Türkçe format)
                value = value.replace(',', '.')
                # Formül kontrolü
                if value.startswith('='):
                    return 0.0
                # Boş veya geçersiz
                if not value or value == '':
                    return 0.0
                return float(value)
            return 0.0
        except Exception as e:
            print(f"⚠️ _safe_float hatası: {value} -> {e}")
            return 0.0