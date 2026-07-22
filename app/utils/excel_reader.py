import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
import re

class ExcelReader:
    """Excel dosyasından veri okuma ve işleme - Güncel başlık desteği ile"""
    
    def __init__(self):
        # ✅ ZORUNLU SÜTUNLAR (Yeni başlıklarla birlikte)
        self.required_columns = [
            'Malzeme_Kodu', 'Ürün Kodu',  # Her ikisi de kabul edilir
            'Mal_Grubu', 'Ürün Grubu',
            'Termin_Suresi', 'Tedarik Süresi (Gün)',
            'Tedarik_Parti_Büyüklügü', 'Sipariş Parti Büyüklüğü'
        ]
        
        # ✅ SÜTUN EŞLEŞTİRME (Eski + Yeni başlıklar)
        self.column_mapping = {
            # Ürün Kodu
            "Malzeme_Kodu": "code",
            "Ürün Kodu": "code",
            
            # Ürün Adı
            "Malzeme_Aciklama": "description",
            "Ürün Adı": "description",
            
            # Ürün Grubu
            "Mal_Grubu": "group",
            "Ürün Grubu": "group",
            
            # Dönem Başı Stok
            "Donem_Basi_Stok": "initial_stock",
            "Dönem Başı Stok": "initial_stock",
            
            # Tedarik Süresi
            "Termin_Suresi": "lead_time_days",
            "Tedarik Süresi (Gün)": "lead_time_days",
            "Tedarik Süresi": "lead_time_days",
            
            # Sipariş Parti Büyüklüğü
            "Tedarik_Parti_Büyüklügü": "eoq",
            "Sipariş Parti Büyüklüğü": "eoq",
            "Parti Büyüklüğü": "eoq",
            
            # Birim Maliyet
            "Birim_Maliyet": "unit_cost",
            "Birim Maliyet (TL)": "unit_cost",
            
            # Stok Tutma Oranı
            "Stok_Tutma_Oranı": "holding_rate",
            "Stok Tutma Oranı (%)": "holding_rate",
            "Stok Tutma Oranı": "holding_rate",
            
            # Stok Tükenme Maliyeti
            "Stok_Tukenme_Maliyeti": "shortage_cost",
            "Stok Tükenme Maliyeti": "shortage_cost",
            
            # Tedarikçi Sayfası
            "Tedarikci_Kodu": "supplier_id",
            "Tedarikçi Kodu": "supplier_id",
            
            "Tedarikci_Adi": "name",
            "Tedarikçi Adı": "name",
            
            "Supplier_Factor": "factor",
            "Tedarikçi Faktörü": "factor",
            
            "OnTimeRate": "ontime_rate",
            "Zamanında Teslim Oranı (%)": "ontime_rate",
            "Zamanında Teslim Oranı": "ontime_rate",
            
            "LT_Ortalama_Gun": "lt_mean",
            "Ortalama Teslim Süresi (Gün)": "lt_mean",
            "Ortalama Teslim Süresi": "lt_mean",
            
            "LT_Std_Gun": "lt_std",
            "Teslim Süresi Standart Sapması": "lt_std",
            "Teslim Süresi Std Sapma": "lt_std",
            
            # Ürün-Tedarikçi Eşleştirme
            "Pay": "share",
            "Tedarik Payı (%)": "share",
            "Tedarik Payı": "share",
            
            "Acik_Bakiye": "open_qty",
            "Açık Sipariş": "open_qty",
            
            "Planli_Termin": "planned_due",
            "Planlanan Teslim Tarihi": "planned_due",
        }
        
        self.min_weeks = 12
        self.max_weeks = 156  # 3 yıl
        
    def _get_column(self, row: pd.Series, *possible_names) -> Any:
        """
        Birden fazla olası sütun adından ilk bulunanı döndürür.
        """
        for name in possible_names:
            if name in row.index and not pd.isna(row.get(name)):
                return row.get(name)
        return None
        
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
            
            # 1. Sheet kontrolü (eski ve yeni isimlerle)
            main_sheet_name = None
            possible_main_sheets = ['Temel_Veriler', 'Ürün Verileri', 'Urun Verileri']
            for sheet_name in possible_main_sheets:
                if sheet_name in sheets:
                    main_sheet_name = sheet_name
                    break
            
            if not main_sheet_name:
                result['errors'].append(
                    "❌ 'Temel_Veriler' veya 'Ürün Verileri' sheet'i bulunamadı!"
                )
                return result
            
            df_main = sheets[main_sheet_name]
            
            # 2. Zorunlu sütun kontrolü (eski veya yeni başlıklardan biri yeterli)
            found_columns = set(df_main.columns)
            required_found = []
            missing_required = []
            
            # Malzeme Kodu kontrolü
            if 'Malzeme_Kodu' in found_columns or 'Ürün Kodu' in found_columns:
                required_found.append('Malzeme_Kodu/Ürün Kodu')
            else:
                missing_required.append('Malzeme_Kodu veya Ürün Kodu')
            
            # Malzeme Grubu kontrolü
            if 'Mal_Grubu' in found_columns or 'Ürün Grubu' in found_columns:
                required_found.append('Mal_Grubu/Ürün Grubu')
            else:
                missing_required.append('Mal_Grubu veya Ürün Grubu')
            
            # Tedarik Süresi kontrolü
            if 'Termin_Suresi' in found_columns or 'Tedarik Süresi (Gün)' in found_columns or 'Tedarik Süresi' in found_columns:
                required_found.append('Termin_Suresi/Tedarik Süresi')
            else:
                missing_required.append('Termin_Suresi veya Tedarik Süresi')
            
            # Parti Büyüklüğü kontrolü
            if 'Tedarik_Parti_Büyüklügü' in found_columns or 'Sipariş Parti Büyüklüğü' in found_columns or 'Parti Büyüklüğü' in found_columns:
                required_found.append('Tedarik_Parti_Büyüklügü/Sipariş Parti Büyüklüğü')
            else:
                missing_required.append('Tedarik_Parti_Büyüklügü veya Sipariş Parti Büyüklüğü')
            
            if missing_required:
                result['errors'].append(f"❌ Eksik zorunlu sütunlar: {', '.join(missing_required)}")
                return result
            
            # 3. W sütunlarını tespit et (W1, W2, ... W15, W16, W17)
            week_cols = self._find_week_columns(df_main.columns)
            print(f"📊 Bulunan hafta sütunları: {week_cols}")
            
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
                        if len(materials) == 1:
                            print(f"📊 İlk malzeme: {material['code']} - {len(material['historical_demand'])} hafta")
                            print(f"📊 İlk 5 değer: {material['historical_demand'][:5]}")
                    else:
                        error_rows.append(idx+2)
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
            
            # 6. Tedarikçi sheet'leri (eski ve yeni isimlerle)
            result['data']['materials'] = materials
            result['data']['week_columns'] = week_cols
            
            # Supplier Mapping sheet
            mapping_sheet_name = None
            possible_mapping_sheets = ['Malzeme_Tedarikciler', 'Ürün-Tedarikçi Eşleştirmeleri', 'Urun-Tedarikci Esleştirmeleri']
            for sheet_name in possible_mapping_sheets:
                if sheet_name in sheets:
                    mapping_sheet_name = sheet_name
                    break
            
            if mapping_sheet_name:
                supplier_mapping = self._process_supplier_mapping(sheets[mapping_sheet_name])
                result['data']['supplier_mapping'] = supplier_mapping
                mapped_codes = set(supplier_mapping.keys())
                material_codes = set(m['code'] for m in materials)
                unmapped = material_codes - mapped_codes
                if unmapped:
                    result['warnings'].append(
                        f"⚠️ {len(unmapped)} malzeme için tedarikçi eşleştirmesi yok: {', '.join(list(unmapped)[:5])}"
                    )
            else:
                result['warnings'].append("ℹ️ Tedarikçi eşleştirme sheet'i bulunamadı. Tek tedarikçi varsayılacak.")
                result['data']['supplier_mapping'] = {}
            
            # Suppliers sheet
            supplier_sheet_name = None
            possible_supplier_sheets = ['Tedarikciler', 'Tedarikçi Bilgileri']
            for sheet_name in possible_supplier_sheets:
                if sheet_name in sheets:
                    supplier_sheet_name = sheet_name
                    break
            
            if supplier_sheet_name:
                suppliers = self._process_suppliers(sheets[supplier_sheet_name])
                result['data']['suppliers'] = suppliers
                if not suppliers:
                    result['warnings'].append("⚠️ Tedarikçi sheet'i boş, varsayılan tedarikçi bilgileri kullanılacak.")
            else:
                result['warnings'].append("ℹ️ 'Tedarikçi Bilgileri' sheet'i bulunamadı. Varsayılan tedarikçi bilgileri kullanılacak.")
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
        """W sütunlarını bul ve sırala (W1, W2, ... W15, W16, W17)"""
        week_cols = []
        for col in columns:
            col_str = str(col).strip().upper()
            # ✅ W ile başlayan ve devamında sayı olan sütunlar
            if col_str.startswith('W') and len(col_str) > 1:
                num_part = col_str[1:]
                # ✅ Sadece sayısal olanları al
                if num_part.isdigit():
                    week_cols.append(col)
        # ✅ Sayısal değere göre sırala (W1, W2, ... W10, W11, W12)
        week_cols.sort(key=lambda x: int(str(x).upper()[1:]))
        return week_cols
    
    def _get_column_value(self, row: pd.Series, *possible_names) -> Any:
        """Birden fazla olası sütun adından ilk bulunanı döndürür"""
        for name in possible_names:
            if name in row.index and not pd.isna(row.get(name)):
                return row.get(name)
        return None
    
    def _process_material_row(self, row: pd.Series, idx: int, week_cols: List[str]) -> Dict:
        """Tek bir malzeme satırını işle - Yeni başlık desteği ile"""
        
        # Malzeme Kodu (eski veya yeni başlık)
        material_code = self._get_column_value(row, 'Malzeme_Kodu', 'Ürün Kodu')
        if not material_code or pd.isna(material_code):
            return None
        material_code = str(material_code).strip()
        
        # 📌 DEBUG
        print(f"\n{'='*60}")
        print(f"🔍 İŞLENİYOR: {material_code}")
        print(f"📊 Toplam W sütunu: {len(week_cols)}")
        
        # 📌 HAFTA VERİLERİNİ Oku
        demand = []
        for week_col in week_cols:
            val = row.get(week_col)
            float_val = self._safe_float(val)
            demand.append(float_val)
        
        print(f"📊 {material_code} - Okunan veri (ilk 12): {demand[:12]}")
        print(f"📊 {material_code} - Veri uzunluğu: {len(demand)}")
        
        # 📌 Sıfır kontrolü
        non_zero = [d for d in demand if d != 0]
        print(f"📊 {material_code} - Sıfır olmayan değer sayısı: {len(non_zero)}/{len(demand)}")
        
        if len(demand) < self.min_weeks:
            print(f"⚠️ {material_code}: {len(demand)} hafta veri var, en az {self.min_weeks} gerekli")
            while len(demand) < self.min_weeks:
                demand.append(0)
            print(f"✅ {material_code}: {len(demand)} haftaya tamamlandı")
        
        # Malzeme grubu (eski veya yeni başlık)
        group = self._get_column_value(row, 'Mal_Grubu', 'Ürün Grubu')
        if not group or pd.isna(group):
            group = 'GENEL'
        group = str(group).strip() or 'GENEL'
        
        # Dönem Başı Stok
        initial_stock = self._get_column_value(row, 'Donem_Basi_Stok', 'Dönem Başı Stok')
        initial_stock = self._safe_float(initial_stock)
        
        # Tedarik Süresi
        lead_time = self._get_column_value(row, 'Termin_Suresi', 'Tedarik Süresi (Gün)', 'Tedarik Süresi')
        lead_time = int(self._safe_float(lead_time) or 14)
        
        # Parti Büyüklüğü
        eoq = self._get_column_value(row, 'Tedarik_Parti_Büyüklügü', 'Sipariş Parti Büyüklüğü', 'Parti Büyüklüğü')
        eoq = int(self._safe_float(eoq) or 100)
        
        # Birim Maliyet
        unit_cost = self._get_column_value(row, 'Birim_Maliyet', 'Birim Maliyet (TL)')
        unit_cost = self._safe_float(unit_cost) or 100.0
        
        # Stok Tutma Oranı
        holding_rate = self._get_column_value(row, 'Stok_Tutma_Oranı', 'Stok Tutma Oranı (%)', 'Stok Tutma Oranı')
        holding_rate = self._safe_float(holding_rate) or 0.2
        
        # Stok Tükenme Maliyeti
        shortage_cost = self._get_column_value(row, 'Stok_Tukenme_Maliyeti', 'Stok Tükenme Maliyeti')
        shortage_cost = self._safe_float(shortage_cost) or 500.0
        
        # Malzeme objesi
        material = {
            'code': material_code,
            'description': self._get_column_value(row, 'Malzeme_Aciklama', 'Ürün Adı') or material_code,
            'group': group,
            'initial_stock': initial_stock,
            'lead_time_days': lead_time,
            'eoq': eoq,
            'unit_cost': unit_cost,
            'holding_rate': holding_rate,
            'shortage_cost': shortage_cost,
            'historical_demand': demand[:self.max_weeks]
        }
        
        print(f"✅ {material_code} işlendi - {len(material['historical_demand'])} hafta")
        print(f"{'='*60}\n")
        
        return material

    def _process_supplier_mapping(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Malzeme-Tedarikçi eşleştirmeleri - Yeni başlık desteği ile"""
        mapping = {}
        
        # Sütunları bul (eski veya yeni)
        material_col = None
        supplier_col = None
        share_col = None
        open_qty_col = None
        planned_due_col = None
        
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in ['Malzeme_Kodu', 'Ürün Kodu']:
                material_col = col
            elif col_str in ['Tedarikci_Kodu', 'Tedarikçi Kodu']:
                supplier_col = col
            elif col_str in ['Pay', 'Tedarik Payı (%)', 'Tedarik Payı']:
                share_col = col
            elif col_str in ['Acik_Bakiye', 'Açık Sipariş']:
                open_qty_col = col
            elif col_str in ['Planli_Termin', 'Planlanan Teslim Tarihi']:
                planned_due_col = col
        
        if not material_col or not supplier_col:
            return mapping
        
        for _, row in df.iterrows():
            material_code = str(row.get(material_col, '')).strip()
            supplier_id = str(row.get(supplier_col, '')).strip()
            if not material_code or not supplier_id:
                continue
            
            if material_code not in mapping:
                mapping[material_code] = []
            
            share = self._safe_float(row.get(share_col, 1.0)) if share_col else 1.0
            open_qty = self._safe_float(row.get(open_qty_col, 0)) if open_qty_col else 0
            planned_due = row.get(planned_due_col, None) if planned_due_col and not pd.isna(row.get(planned_due_col)) else None
            
            mapping[material_code].append({
                'supplier_id': supplier_id,
                'share': share,
                'open_qty': open_qty,
                'planned_due': planned_due
            })
        return mapping
    
    def _process_suppliers(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """Tedarikçi bilgileri - Yeni başlık desteği ile"""
        suppliers = {}
        
        # Sütunları bul
        supplier_col = None
        name_col = None
        factor_col = None
        ontime_col = None
        lt_mean_col = None
        lt_std_col = None
        
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in ['Tedarikci_Kodu', 'Tedarikçi Kodu']:
                supplier_col = col
            elif col_str in ['Tedarikci_Adi', 'Tedarikçi Adı']:
                name_col = col
            elif col_str in ['Supplier_Factor', 'Tedarikçi Faktörü']:
                factor_col = col
            elif col_str in ['OnTimeRate', 'Zamanında Teslim Oranı (%)', 'Zamanında Teslim Oranı']:
                ontime_col = col
            elif col_str in ['LT_Ortalama_Gun', 'Ortalama Teslim Süresi (Gün)', 'Ortalama Teslim Süresi']:
                lt_mean_col = col
            elif col_str in ['LT_Std_Gun', 'Teslim Süresi Standart Sapması', 'Teslim Süresi Std Sapma']:
                lt_std_col = col
        
        if not supplier_col:
            return suppliers
        
        for _, row in df.iterrows():
            supplier_id = str(row.get(supplier_col, '')).strip()
            if not supplier_id:
                continue
            
            suppliers[supplier_id] = {
                'name': str(row.get(name_col, supplier_id)) if name_col else supplier_id,
                'factor': self._safe_float(row.get(factor_col, 1.0)) if factor_col else 1.0,
                'ontime_rate': self._safe_float(row.get(ontime_col, 0.8)) if ontime_col else 0.8,
                'lt_mean': self._safe_float(row.get(lt_mean_col, 14)) if lt_mean_col else 14,
                'lt_std': self._safe_float(row.get(lt_std_col, 3)) if lt_std_col else 3
            }
        return suppliers
    
    def _safe_float(self, value) -> float:
        """Güvenli float dönüşümü"""
        try:
            if pd.isna(value) or value is None:
                return 0.0
            if isinstance(value, (int, float)):
                if np.isnan(value) or np.isinf(value):
                    return 0.0
                return float(value)
            if isinstance(value, str):
                value = str(value).strip()
                if value.startswith('='):
                    return 0.0
                value = value.replace(',', '.').replace(' ', '')
                return float(value) if value else 0.0
            return 0.0
        except:
            return 0.0