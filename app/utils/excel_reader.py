import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re

class ExcelReader:
    """Excel dosyasından veri okuma ve işleme"""
    
    def __init__(self):
        self.required_columns = [
            'Malzeme_Kodu', 'Mal_Grubu', 'Termin_Suresi', 'Tedarik_Parti_Büyüklügü'
        ]
        self.min_weeks = 12
        
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Excel dosyasını oku ve tüm sheet'leri işle"""
        try:
            # Tüm sheet'leri oku
            sheets = pd.read_excel(file_path, sheet_name=None, header=0)
            
            result = {
                'success': False,
                'data': {},
                'errors': [],
                'warnings': [],
                'summary': {}
            }
            
            # Temel_Veriler sheet'ini kontrol et
            if 'Temel_Veriler' not in sheets:
                result['errors'].append("'Temel_Veriler' sheet'i bulunamadı!")
                return result
            
            df_main = sheets['Temel_Veriler']
            
            # Zorunlu sütunları kontrol et
            missing_cols = [col for col in self.required_columns if col not in df_main.columns]
            if missing_cols:
                result['errors'].append(f"Eksik sütunlar: {', '.join(missing_cols)}")
                return result
            
            # W sütunlarını tespit et
            week_cols = self._find_week_columns(df_main.columns)
            if len(week_cols) < self.min_weeks:
                result['errors'].append(f"Yetersiz W sütunu: {len(week_cols)} hafta (en az {self.min_weeks} gerekli)")
                return result
            
            # Verileri işle
            materials = []
            error_count = 0
            
            for idx, row in df_main.iterrows():
                try:
                    material = self._process_material_row(row, idx, week_cols)
                    if material:
                        materials.append(material)
                    else:
                        error_count += 1
                except Exception as e:
                    result['errors'].append(f"Satır {idx+2}: {str(e)}")
                    error_count += 1
            
            if not materials:
                result['errors'].append("Hiç geçerli malzeme bulunamadı!")
                return result
            
            result['data']['materials'] = materials
            result['data']['week_columns'] = week_cols
            
            # Malzeme_Tedarikciler sheet'ini kontrol et
            if 'Malzeme_Tedarikciler' in sheets:
                supplier_mapping = self._process_supplier_mapping(sheets['Malzeme_Tedarikciler'])
                result['data']['supplier_mapping'] = supplier_mapping
            else:
                result['warnings'].append("'Malzeme_Tedarikciler' sheet'i bulunamadı. Tek tedarikçi varsayılacak.")
                result['data']['supplier_mapping'] = {}
            
            # Tedarikciler sheet'ini kontrol et
            if 'Tedarikciler' in sheets:
                suppliers = self._process_suppliers(sheets['Tedarikciler'])
                result['data']['suppliers'] = suppliers
            else:
                result['warnings'].append("'Tedarikciler' sheet'i bulunamadı. Varsayılan tedarikçi bilgileri kullanılacak.")
                result['data']['suppliers'] = {}
            
            # Özet bilgiler
            result['summary'] = {
                'total_materials': len(materials),
                'total_weeks': len(week_cols),
                'errors': error_count,
                'has_suppliers': 'suppliers' in result['data'] and bool(result['data']['suppliers']),
                'has_mapping': 'supplier_mapping' in result['data'] and bool(result['data']['supplier_mapping'])
            }
            
            result['success'] = True
            return result
            
        except Exception as e:
            return {
                'success': False,
                'data': {},
                'errors': [f"Excel okuma hatası: {str(e)}"],
                'warnings': [],
                'summary': {}
            }
    
    def _find_week_columns(self, columns: List[str]) -> List[str]:
        """W sütunlarını bul ve sırala"""
        week_cols = []
        for col in columns:
            col_str = str(col).strip().upper()
            if col_str.startswith('W') and len(col_str) > 1:
                # W'den sonraki kısmı al
                num_part = col_str[1:]
                if num_part.isdigit():
                    week_cols.append(col)
        
        # Sayısal sıraya göre sırala
        week_cols.sort(key=lambda x: int(str(x).upper()[1:]) if str(x).upper()[1:].isdigit() else 0)
        return week_cols
    
    def _process_material_row(self, row: pd.Series, idx: int, week_cols: List[str]) -> Dict:
        """Tek bir malzeme satırını işle"""
        try:
            material_code = str(row.get('Malzeme_Kodu', '')).strip()
            if not material_code or pd.isna(material_code):
                return None
            
            # Malzeme bilgileri
            material = {
                'code': material_code,
                'description': str(row.get('Malzeme_Aciklama', material_code)),
                'group': str(row.get('Mal_Grubu', 'GENEL')),
                'initial_stock': self._safe_float(row.get('Donem_Basi_Stok', 0)),
                'lead_time_days': int(self._safe_float(row.get('Termin_Suresi', 14))),
                'eoq': int(self._safe_float(row.get('Tedarik_Parti_Büyüklügü', 100))),
                'unit_cost': self._safe_float(row.get('Birim_Maliyet', 100)),
                'holding_rate': self._safe_float(row.get('Stok_Tutma_Oranı', 0.2)),
                'shortage_cost': self._safe_float(row.get('Stok_Tukenme_Maliyeti', 500)),
                'historical_demand': []
            }
            
            # Haftalık talepleri al
            for week_col in week_cols:
                val = row.get(week_col)
                demand = self._safe_float(val)
                material['historical_demand'].append(max(0, demand))
            
            # En az 12 hafta veri kontrolü
            if len(material['historical_demand']) < self.min_weeks:
                return None
            
            return material
            
        except Exception as e:
            print(f"Satır {idx+2} işlenirken hata: {e}")
            return None
    
    def _process_supplier_mapping(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Malzeme-Tedarikçi eşleştirmelerini işle"""
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
        """Tedarikçi bilgilerini işle"""
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
        """Güvenli float dönüşümü"""
        try:
            if pd.isna(value) or value is None:
                return 0.0
            if isinstance(value, (int, float)):
                return float(value) if not np.isinf(value) and not np.isnan(value) else 0.0
            if isinstance(value, str):
                # Excel formülleri varsa temizle
                value = str(value).strip()
                if value.startswith('='):
                    # Formül içinse 0 döndür (şimdilik)
                    return 0.0
                value = value.replace(',', '.').replace(' ', '')
                return float(value) if value else 0.0
            return 0.0
        except:
            return 0.0