# app/utils/excel_reader.py
"""
Excel Reader - Excel dosyasını okur, başlık satırını tespit eder,
verileri canonical formata dönüştürür.
"""

import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Union
import re
import unicodedata

logger = logging.getLogger(__name__)


class ExcelReader:
    """
    Excel dosyasını okur ve sheet'leri ayrı ayrı döndürür.
    Başlık satırını otomatik tespit eder.
    """

    def __init__(self):
        # Sheet adı eşleştirmesi (Excel'deki isim -> internal key)
        self.sheet_mapping = {
            'Temel_Veriler': 'materials',
            'Tedarikciler': 'suppliers',
            'Malzeme_Tedarikciler': 'supplier_mapping',
        }
        
        # Kolon eşleştirme (normalize edilmiş anahtar -> hedef)
        self.column_mapping = {
            # Temel_Veriler
            'urun kodu': 'Ürün Kodu',
            'ürün kodu': 'Ürün Kodu',
            'product code': 'Ürün Kodu',
            'product_code': 'Ürün Kodu',
            'productcode': 'Ürün Kodu',
            'kod': 'Ürün Kodu',
            'code': 'Ürün Kodu',
            
            'urun adi': 'Ürün Adı',
            'ürün adı': 'Ürün Adı',
            'product name': 'Ürün Adı',
            'product_name': 'Ürün Adı',
            'aciklama': 'Ürün Adı',
            'description': 'Ürün Adı',
            
            'urun grubu': 'Ürün Grubu',
            'ürün grubu': 'Ürün Grubu',
            'product group': 'Ürün Grubu',
            'group': 'Ürün Grubu',
            
            'donem basi stok': 'Dönem Başı Stok',
            'dönem başı stok': 'Dönem Başı Stok',
            'initial stock': 'Dönem Başı Stok',
            'initial_stock': 'Dönem Başı Stok',
            'baslangic stok': 'Dönem Başı Stok',
            'başlangıç stok': 'Dönem Başı Stok',
            
            'tedarik suresi (gun)': 'Tedarik Süresi (Gün)',
            'tedarik süresi (gün)': 'Tedarik Süresi (Gün)',
            'tedarik suresi': 'Tedarik Süresi (Gün)',
            'tedarik süresi': 'Tedarik Süresi (Gün)',
            'lead time': 'Tedarik Süresi (Gün)',
            'lead_time': 'Tedarik Süresi (Gün)',
            'teslim suresi': 'Tedarik Süresi (Gün)',
            'teslim süresi': 'Tedarik Süresi (Gün)',
            
            'siparis parti buyuklugu': 'Sipariş Parti Büyüklüğü',
            'sipariş parti büyüklüğü': 'Sipariş Parti Büyüklüğü',
            'eoq': 'Sipariş Parti Büyüklüğü',
            'parti buyuklugu': 'Sipariş Parti Büyüklüğü',
            'parti büyüklüğü': 'Sipariş Parti Büyüklüğü',
            'moq': 'Sipariş Parti Büyüklüğü',
            
            'birim maliyet (tl)': 'Birim Maliyet (TL)',
            'birim maliyet': 'Birim Maliyet (TL)',
            'unit cost': 'Birim Maliyet (TL)',
            'unit_cost': 'Birim Maliyet (TL)',
            'maliyet': 'Birim Maliyet (TL)',
            'cost': 'Birim Maliyet (TL)',
            
            'stok tutma orani (%)': 'Stok Tutma Oranı (%)',
            'stok tutma oranı (%)': 'Stok Tutma Oranı (%)',
            'holding rate': 'Stok Tutma Oranı (%)',
            'holding_rate': 'Stok Tutma Oranı (%)',
            'tutma orani': 'Stok Tutma Oranı (%)',
            'tutma oranı': 'Stok Tutma Oranı (%)',
            
            'stok tukenme maliyeti': 'Stok Tükenme Maliyeti',
            'stok tükenme maliyeti': 'Stok Tükenme Maliyeti',
            'shortage cost': 'Stok Tükenme Maliyeti',
            'shortage_cost': 'Stok Tükenme Maliyeti',
            'tukenme maliyeti': 'Stok Tükenme Maliyeti',
            'tükenme maliyeti': 'Stok Tükenme Maliyeti',
            
            # Tedarikciler
            'tedarikci kodu': 'Tedarikçi Kodu',
            'tedarikçi kodu': 'Tedarikçi Kodu',
            'supplier code': 'Tedarikçi Kodu',
            'supplier_code': 'Tedarikçi Kodu',
            'supplier id': 'Tedarikçi Kodu',
            'supplier_id': 'Tedarikçi Kodu',
            
            'tedarikci adi': 'Tedarikçi Adı',
            'tedarikçi adı': 'Tedarikçi Adı',
            'supplier name': 'Tedarikçi Adı',
            'supplier_name': 'Tedarikçi Adı',
            'tedarikci': 'Tedarikçi Adı',
            'supplier': 'Tedarikçi Adı',
            
            'tedarikci faktoru': 'Tedarikçi Faktörü',
            'tedarikçi faktörü': 'Tedarikçi Faktörü',
            'supplier factor': 'Tedarikçi Faktörü',
            'factor': 'Tedarikçi Faktörü',
            
            'zamaninda teslim orani (%)': 'Zamanında Teslim Oranı (%)',
            'zamanında teslim oranı (%)': 'Zamanında Teslim Oranı (%)',
            'ontime rate': 'Zamanında Teslim Oranı (%)',
            'ontime_rate': 'Zamanında Teslim Oranı (%)',
            'teslim orani': 'Zamanında Teslim Oranı (%)',
            'teslim oranı': 'Zamanında Teslim Oranı (%)',
            
            'ortalama teslim suresi (gun)': 'Ortalama Teslim Süresi (Gün)',
            'ortalama teslim süresi (gün)': 'Ortalama Teslim Süresi (Gün)',
            'average lead time': 'Ortalama Teslim Süresi (Gün)',
            'lt_mean': 'Ortalama Teslim Süresi (Gün)',
            'ortalama teslim': 'Ortalama Teslim Süresi (Gün)',
            
            'teslim suresi standart sapmasi': 'Teslim Süresi Standart Sapması',
            'teslim süresi standart sapması': 'Teslim Süresi Standart Sapması',
            'lead time std': 'Teslim Süresi Standart Sapması',
            'lt_std': 'Teslim Süresi Standart Sapması',
            'standart sapma': 'Teslim Süresi Standart Sapması',
            
            # Malzeme_Tedarikciler
            'tedarik payi (%)': 'Tedarik Payı (%)',
            'tedarik payı (%)': 'Tedarik Payı (%)',
            'supplier share': 'Tedarik Payı (%)',
            'share': 'Tedarik Payı (%)',
            'pay': 'Tedarik Payı (%)',
            
            'acik siparis': 'Açık Sipariş',
            'açık sipariş': 'Açık Sipariş',
            'open order': 'Açık Sipariş',
            'open_qty': 'Açık Sipariş',
            'open qty': 'Açık Sipariş',
            
            'planlanan teslim tarihi': 'Planlanan Teslim Tarihi',
            'planned delivery': 'Planlanan Teslim Tarihi',
            'planned_due': 'Planlanan Teslim Tarihi',
            'teslim tarihi': 'Planlanan Teslim Tarihi',
        }
        
        # Anahtar kelimeler (başlık satırı tespiti için)
        self.header_keywords = [
            'ürün kodu', 'tedarikçi kodu', 'ürün adı', 'tedarikçi adı',
            'dönem başı stok', 'tedarik süresi', 'sipariş parti büyüklüğü',
            'birim maliyet', 'stok tutma oranı', 'stok tükenme maliyeti',
            'zamanında teslim oranı', 'ortalama teslim süresi',
            'tedarik payı', 'açık sipariş', 'planlanan teslim tarihi',
            'w1', 'w2', 'w3', 'w4', 'w5', 'w6', 'w7', 'w8', 'w9',
            'w10', 'w11', 'w12', 'w13', 'w14', 'w15', 'w16'
        ]

    def _normalize_text(self, text: str) -> str:
        """
        Metni normalize eder:
        - Küçük harfe çevir
        - Türkçe karakterleri normalleştir
        - Gereksiz boşlukları temizle
        - Parantez içindekileri temizle (opsiyonel)
        """
        if not text:
            return ''
        
        # Küçük harfe çevir
        text = text.lower().strip()
        
        # Unicode normalizasyonu (ç, ğ, ı, ö, ş, ü -> c, g, i, o, s, u)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        
        # Parantez içindekileri temizle (örnek: "Tedarik Süresi (Gün)" -> "tedarik suresi")
        text = re.sub(r'\([^)]*\)', '', text).strip()
        
        # Birden fazla boşluğu tek boşluğa çevir
        text = re.sub(r'\s+', ' ', text)
        
        return text

    def _find_matching_column(self, header: str, target: str) -> bool:
        """
        Bir başlığın hedef kolonla eşleşip eşleşmediğini kontrol eder.
        """
        if not header or not target:
            return False
        
        # Normalize et
        header_norm = self._normalize_text(str(header))
        target_norm = self._normalize_text(target)
        
        # Tam eşleşme
        if header_norm == target_norm:
            return True
        
        # Biri diğerini içeriyor mu?
        if target_norm in header_norm or header_norm in target_norm:
            return True
        
        return False

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Excel dosyasını okur ve tüm sheet'leri döndürür.
        
        Returns:
            {
                'success': True,
                'data': {
                    'materials': [...],
                    'suppliers': {...},
                    'supplier_mapping': {...}
                },
                'sheet_names': [...]
            }
        """
        try:
            # Tüm sheet'leri oku (header=None ile ham veri)
            excel_data = pd.read_excel(file_path, sheet_name=None, header=None)
            
            result = {}
            sheet_names = []
            
            for sheet_name, df in excel_data.items():
                sheet_names.append(sheet_name)
                
                # Sheet adını canonical'e çevir
                canonical_name = self.sheet_mapping.get(sheet_name, sheet_name)
                
                # Başlık satırını tespit et
                header_row = self._find_header_row(df)
                
                if header_row is None:
                    # Başlık bulunamadı, tüm satırları ham veri olarak al
                    result[canonical_name] = df.values.tolist()
                    continue
                
                # Başlık satırını kolon ismi olarak kullan
                headers = df.iloc[header_row].values.tolist()
                # Temizlenmiş başlıklar
                clean_headers = []
                for h in headers:
                    if pd.isna(h):
                        clean_headers.append('')
                    else:
                        clean_headers.append(str(h).strip())
                
                # 🔍 DEBUG: Başlıkları yazdır
                print(f"🔍 {sheet_name} başlıkları: {clean_headers[:10]}...")
                
                # Veri satırları (başlıktan sonraki satırlar)
                data_rows = df.iloc[header_row + 1:].values.tolist()
                
                # Boş satırları filtrele
                clean_rows = []
                for row in data_rows:
                    has_data = False
                    clean_row = []
                    for cell in row:
                        if pd.isna(cell):
                            clean_row.append(None)
                        elif isinstance(cell, str):
                            cleaned = cell.strip()
                            clean_row.append(cleaned if cleaned else None)
                            if cleaned:
                                has_data = True
                        else:
                            clean_row.append(cell)
                            has_data = True
                    
                    if has_data:
                        clean_rows.append(clean_row)
                
                # Özel işlemler
                if canonical_name == 'materials':
                    result[canonical_name] = self._process_materials(clean_headers, clean_rows)
                elif canonical_name == 'suppliers':
                    result[canonical_name] = self._process_suppliers(clean_headers, clean_rows)
                elif canonical_name == 'supplier_mapping':
                    result[canonical_name] = self._process_supplier_mapping(clean_headers, clean_rows)
                else:
                    # Genel işlem
                    result[canonical_name] = []
                    for row in clean_rows:
                        row_dict = {}
                        for idx, header in enumerate(clean_headers):
                            if idx < len(row):
                                row_dict[header] = row[idx]
                        if row_dict:
                            result[canonical_name].append(row_dict)
            
            # 🔍 DEBUG
            print(f"🔍 ExcelReader sonucu:")
            for key, value in result.items():
                if isinstance(value, list):
                    print(f"   {key}: {len(value)} satır")
                elif isinstance(value, dict):
                    print(f"   {key}: {len(value)} anahtar")
                else:
                    print(f"   {key}: {type(value)}")
            
            return {
                'success': True,
                'data': result,
                'sheet_names': sheet_names
            }
            
        except Exception as e:
            logger.error(f"Excel okuma hatası: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }

    def _find_header_row(self, df: pd.DataFrame) -> Optional[int]:
        """
        Başlık satırını bulur.
        """
        max_rows = min(10, len(df))
        
        for idx in range(max_rows):
            row = df.iloc[idx].values.tolist()
            
            row_str = []
            for cell in row:
                if pd.isna(cell):
                    row_str.append('')
                else:
                    row_str.append(str(cell).strip())
            
            if all(cell == '' for cell in row_str):
                continue
            
            row_text = ' '.join(row_str).lower()
            
            # Anahtar kelime eşleşmesi
            keyword_matches = 0
            for keyword in self.header_keywords:
                if keyword in row_text:
                    keyword_matches += 1
            
            if keyword_matches >= 2:
                return idx
            
            # String oranı
            string_count = sum(1 for cell in row_str if cell != '')
            if len(row_str) > 0 and string_count / len(row_str) > 0.6:
                numeric_count = 0
                for cell in row_str:
                    if cell and re.match(r'^[\d.,]+$', cell):
                        numeric_count += 1
                
                if numeric_count / len(row_str) < 0.3:
                    return idx
        
        return None

    def _get_column_indices(self, headers: List[str], target_columns: List[str]) -> Dict[str, int]:
        """
        Kolon indekslerini bulur. Önce direkt eşleşme, sonra mapping üzerinden dener.
        """
        result = {}
        
        # Headers'ı temizle
        clean_headers = []
        for h in headers:
            if h is None:
                clean_headers.append('')
            else:
                clean_headers.append(str(h).strip())
        
        for target in target_columns:
            found = False
            
            # 1. Önce mapping üzerinden eşleşme dene
            target_lower = self._normalize_text(target)
            for header in clean_headers:
                header_lower = self._normalize_text(header)
                if header_lower == target_lower:
                    idx = clean_headers.index(header)
                    result[target] = idx
                    found = True
                    print(f"✅ '{target}' -> '{header}' (mapping ile eşleşti)")
                    break
            
            if found:
                continue
            
            # 2. column_mapping'te ara
            for header in clean_headers:
                if not header:
                    continue
                header_lower = self._normalize_text(header)
                
                # Mapping'te bu header var mı?
                if header_lower in self.column_mapping:
                    mapped_target = self.column_mapping[header_lower]
                    if mapped_target == target:
                        idx = clean_headers.index(header)
                        result[target] = idx
                        found = True
                        print(f"✅ '{target}' -> '{header}' (column_mapping ile eşleşti)")
                        break
                
                # Mapping'teki anahtarları da dene
                for key, mapped_target in self.column_mapping.items():
                    if mapped_target == target:
                        if key in header_lower or header_lower in key:
                            idx = clean_headers.index(header)
                            result[target] = idx
                            found = True
                            print(f"✅ '{target}' -> '{header}' (kısmi eşleşme: '{key}')")
                            break
                if found:
                    break
            
            if not found:
                # 3. Son çare: direkt kelime eşleşmesi
                target_words = target.lower().split()
                for header in clean_headers:
                    if not header:
                        continue
                    header_lower = header.lower()
                    # Tüm kelimeler header'da var mı?
                    all_words_found = all(word in header_lower for word in target_words)
                    if all_words_found:
                        idx = clean_headers.index(header)
                        result[target] = idx
                        found = True
                        print(f"✅ '{target}' -> '{header}' (kelime eşleşmesi)")
                        break
                
                if not found:
                    result[target] = None
                    print(f"❌ '{target}' eşleşemedi! Mevcut başlıklar: {clean_headers[:10]}")
        
        return result

# app/utils/excel_reader.py - _process_materials DÜZELTİLDİ

# app/utils/excel_reader.py - _process_materials DÜZELTİLDİ

    def _process_materials(self, headers: List[str], rows: List[List]) -> List[Dict[str, Any]]:
        """Temel_Veriler sheet'ini işler."""
        result = []
        
        print(f"🔍 _process_materials: headers = {headers[:10]}...")
        print(f"🔍 _process_materials: {len(rows)} satır")
        
        # Kolon indekslerini bul
        col_indices = self._get_column_indices(headers, [
            'Ürün Kodu', 'Ürün Adı', 'Ürün Grubu', 'Dönem Başı Stok',
            'Tedarik Süresi (Gün)', 'Sipariş Parti Büyüklüğü',
            'Birim Maliyet (TL)', 'Stok Tutma Oranı (%)', 'Stok Tükenme Maliyeti'
        ])
        
        print(f"🔍 Kolon indeksleri: {col_indices}")
        
        # W kolonlarını bul
        week_indices = []
        for idx, header in enumerate(headers):
            if isinstance(header, str):
                header_upper = header.upper().strip()
                # W1, W2, ... W12, W13 formatları
                if header_upper.startswith('W'):
                    try:
                        week_num = int(header_upper[1:])
                        if 1 <= week_num <= 52:
                            week_indices.append((idx, week_num))
                    except ValueError:
                        match = re.match(r'W(\d+)', header_upper)
                        if match:
                            week_num = int(match.group(1))
                            if 1 <= week_num <= 52:
                                week_indices.append((idx, week_num))
        
        week_indices.sort(key=lambda x: x[1])
        print(f"🔍 W kolonları: {len(week_indices)} adet")
        
        for row_idx, row in enumerate(rows):
            # Ürün Kodu kontrolü
            product_code_idx = col_indices.get('Ürün Kodu')
            product_code = None
            
            if product_code_idx is not None and product_code_idx < len(row):
                product_code = row[product_code_idx]
            
            # Ürün Kodu boş olabilir, bu bir hata ama satırı atlamamalıyız
            if product_code is None or str(product_code).strip() == '':
                print(f"⚠️ {row_idx + 1}. satırda Ürün Kodu BOŞ! (Bu bir veri hatası, ancak satır atlanmayacak)")
                product_code = None
            
            # Satırda en az bir geçerli veri var mı?
            has_valid_data = False
            
            # Ürün Adı kontrolü
            description_idx = col_indices.get('Ürün Adı')
            if description_idx is not None and description_idx < len(row):
                description = row[description_idx]
                if description is not None and str(description).strip() != '':
                    has_valid_data = True
            
            # W verileri kontrolü
            if not has_valid_data:
                for idx, _ in week_indices:
                    if idx < len(row):
                        value = row[idx]
                        if value is not None and str(value).strip() != '' and str(value).strip() != '0':
                            has_valid_data = True
                            break
            
            if not has_valid_data:
                print(f"⚠️ {row_idx + 1}. satır tamamen boş, atlanıyor.")
                continue
            
            # ============================================================
            # RAW VALUE PRESERVATION
            # ============================================================
            material = {
                'product_code': str(product_code).strip() if product_code is not None else None,
                'description': self._get_cell(row, col_indices.get('Ürün Adı')),
                'group': self._get_cell(row, col_indices.get('Ürün Grubu')),
                'initial_stock': self._get_raw_value(row, col_indices.get('Dönem Başı Stok')),
                'lead_time_days': self._get_raw_value(row, col_indices.get('Tedarik Süresi (Gün)')),
                'eoq': self._get_raw_value(row, col_indices.get('Sipariş Parti Büyüklüğü')),
                'unit_cost': self._get_raw_value(row, col_indices.get('Birim Maliyet (TL)')),
                'holding_rate': self._get_raw_value(row, col_indices.get('Stok Tutma Oranı (%)')),
                'shortage_cost': self._get_raw_value(row, col_indices.get('Stok Tükenme Maliyeti')),
            }
            
            # ============================================================
            # W kolonlarını ekle - RAW VALUE PRESERVATION
            # historical_demand ve weekly_data aynı veriyi içerir
            # ============================================================
            weekly_data = []
            has_weekly_data = False
            
            for idx, week_num in week_indices:
                if idx < len(row):
                    value = row[idx]
                    # Excel formülü ise None bırak
                    if isinstance(value, str) and value.startswith('='):
                        weekly_data.append(None)
                    else:
                        # Ham değeri koru
                        weekly_data.append(value)
                        if value is not None and str(value).strip() != '' and str(value).strip() != '0':
                            has_weekly_data = True
                else:
                    weekly_data.append(None)
            
            # ✅ Eğer hiç W verisi yoksa, bu satırı atlama ama uyarı ver
            if not has_weekly_data:
                print(f"⚠️ {row_idx + 1}. satırda W verisi yok! (product_code={material['product_code']})")
            
            # ✅ historical_demand ve weekly_data'yı aynı veriyle doldur
            material['historical_demand'] = weekly_data
            material['weekly_data'] = weekly_data
            
            # Eğer Ürün Kodu boşsa, bunu bir hata olarak işaretle
            if material['product_code'] is None:
                material['_missing_code'] = True
                material['_row_number'] = row_idx + 1
            
            result.append(material)
        
        print(f"🔍 materials işlendi: {len(result)} satır")
        if result:
            print(f"   İlk satır: product_code={result[0].get('product_code')!r}, unit_cost={result[0].get('unit_cost')!r}, holding_rate={result[0].get('holding_rate')!r}")
            print(f"   İlk satır W verileri: {result[0].get('weekly_data', [])[:5]!r}")
        
        return result
    
    def _get_numeric_from_value(self, value: Any) -> Optional[float]:
        """Bir değeri sayısal olarak dönüştürmeye çalışır."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = value.strip()
            if not cleaned:
                return None
            if cleaned.startswith('='):
                return None
            try:
                # Türkçe format dönüşümleri
                if '.' in cleaned and ',' in cleaned:
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                elif ',' in cleaned and '.' in cleaned:
                    cleaned = cleaned.replace(',', '')
                elif ',' in cleaned and '.' not in cleaned:
                    cleaned = cleaned.replace(',', '.')
                elif '.' in cleaned and ',' not in cleaned:
                    # Belirsiz: 10.000 (on bin mi, on virgül sıfır mı?)
                    # Varsayılan olarak binlik ayraç kabul et
                    cleaned = cleaned.replace('.', '')
                return float(cleaned)
            except:
                return None
        return None

# app/utils/excel_reader.py - _process_suppliers DÜZELTİLDİ

    def _process_suppliers(self, headers: List[str], rows: List[List]) -> Dict[str, Any]:
        """Tedarikciler sheet'ini işler."""
        result = {}
        
        col_indices = self._get_column_indices(headers, [
            'Tedarikçi Kodu', 'Tedarikçi Adı', 'Tedarikçi Faktörü',
            'Zamanında Teslim Oranı (%)', 'Ortalama Teslim Süresi (Gün)',
            'Teslim Süresi Standart Sapması'
        ])
        
        print(f"🔍 Suppliers kolon indeksleri: {col_indices}")
        
        for row_idx, row in enumerate(rows):
            # ✅ row'un liste olduğundan emin ol
            if not isinstance(row, list):
                print(f"⚠️ {row_idx}. satır liste değil: {type(row)} - atlanıyor")
                continue
            
            supplier_code_idx = col_indices.get('Tedarikçi Kodu')
            if supplier_code_idx is None or supplier_code_idx >= len(row):
                print(f"⚠️ {row_idx}. satırda Tedarikçi Kodu indeksi geçersiz")
                continue
            
            supplier_code = row[supplier_code_idx]
            if supplier_code is None or str(supplier_code).strip() == '':
                print(f"⚠️ {row_idx}. satırda Tedarikçi Kodu BOŞ - atlanıyor")
                continue
            
            supplier_code = str(supplier_code).strip()
            
            result[supplier_code] = {
                'name': self._get_cell(row, col_indices.get('Tedarikçi Adı')),
                'factor': self._get_numeric(row, col_indices.get('Tedarikçi Faktörü'), default=1.0),
                'ontime_rate': self._get_numeric(row, col_indices.get('Zamanında Teslim Oranı (%)'), default=0),
                'lt_mean': self._get_numeric(row, col_indices.get('Ortalama Teslim Süresi (Gün)')),
                'lt_std': self._get_numeric(row, col_indices.get('Teslim Süresi Standart Sapması')),
            }
        
        print(f"🔍 suppliers işlendi: {len(result)} tedarikçi")
        return result

    def _process_supplier_mapping(self, headers: List[str], rows: List[List]) -> Dict[str, Any]:
        """Malzeme_Tedarikciler sheet'ini işler."""
        result = {}
        
        col_indices = self._get_column_indices(headers, [
            'Ürün Kodu', 'Tedarikçi Kodu', 'Tedarik Payı (%)',
            'Açık Sipariş', 'Planlanan Teslim Tarihi'
        ])
        
        print(f"🔍 Supplier mapping kolon indeksleri: {col_indices}")
        
        for row_idx, row in enumerate(rows):
            if not isinstance(row, list):
                print(f"⚠️ {row_idx}. satır liste değil: {type(row)} - atlanıyor")
                continue
            
            product_code_idx = col_indices.get('Ürün Kodu')
            supplier_code_idx = col_indices.get('Tedarikçi Kodu')
            
            if product_code_idx is None or product_code_idx >= len(row):
                print(f"⚠️ {row_idx}. satırda Ürün Kodu indeksi geçersiz")
                continue
            if supplier_code_idx is None or supplier_code_idx >= len(row):
                print(f"⚠️ {row_idx}. satırda Tedarikçi Kodu indeksi geçersiz")
                continue
            
            product_code = row[product_code_idx]
            supplier_code = row[supplier_code_idx]
            
            if product_code is None or str(product_code).strip() == '':
                print(f"⚠️ {row_idx}. satırda Ürün Kodu BOŞ - atlanıyor")
                continue
            if supplier_code is None or str(supplier_code).strip() == '':
                print(f"⚠️ {row_idx}. satırda Tedarikçi Kodu BOŞ - atlanıyor")
                continue
            
            product_code = str(product_code).strip()
            supplier_code = str(supplier_code).strip()
            
            if product_code not in result:
                result[product_code] = []
            
            # ✅ share değerini doğru al (yüzde olarak)
            share_value = row[col_indices.get('Tedarik Payı (%)')] if col_indices.get('Tedarik Payı (%)') is not None and col_indices.get('Tedarik Payı (%)') < len(row) else 100
            try:
                share = float(share_value) / 100 if share_value else 1.0
            except:
                share = 1.0
            
            result[product_code].append({
                'supplier_id': supplier_code,
                'share': share,
                'open_qty': self._get_numeric(row, col_indices.get('Açık Sipariş'), default=0),
                'planned_due': self._get_cell(row, col_indices.get('Planlanan Teslim Tarihi')),
            })
        
        print(f"🔍 supplier_mapping işlendi: {len(result)} ürün")
        return result

    def _get_cell(self, row: List, idx: Optional[int]) -> Optional[str]:
        """Hücre değerini string olarak alır."""
        if idx is None or idx >= len(row):
            return None
        value = row[idx]
        if value is None or pd.isna(value):
            return None
        if isinstance(value, str):
            cleaned = value.strip()
            return cleaned if cleaned else None
        return str(value)

    def _get_raw_value(self, row: List, idx: Optional[int]) -> Any:
            """
            Hücre değerini ham olarak alır.
            Hiçbir dönüşüm yapmaz, sadece None/NaN kontrolü yapar.
            Validasyon engine'i dönüşümü yapacaktır.
            """
            if idx is None or idx >= len(row):
                return None
            
            value = row[idx]
            
            # None veya NaN kontrolü
            if value is None:
                return None
            
            # pandas NaN kontrolü
            try:
                import pandas as pd
                if pd.isna(value):
                    return None
            except:
                pass
            
            # Ham değeri olduğu gibi döndür
            # - Eğer string ise (örn: "asd", "125,50") string olarak döner
            # - Eğer int/float ise sayısal olarak döner
            # - Eğer bool ise bool olarak döner
            return value

    def _get_numeric(self, row: List, idx: Optional[int], default: Optional[float] = None) -> Optional[float]:
            """
            Hücre değerini sayısal olarak alır.
            SADECE VALID NUMERIC VALUE için kullanılır.
            Eğer değer numeric değilse None döndürür.
            """
            if idx is None or idx >= len(row):
                return default
            
            value = row[idx]
            
            if value is None:
                return default
            
            try:
                import pandas as pd
                if pd.isna(value):
                    return default
            except:
                pass
            
            if isinstance(value, (int, float)):
                return float(value)
            
            if isinstance(value, str):
                cleaned = value.strip()
                if not cleaned:
                    return default
                
                if cleaned.startswith('='):
                    return default
                
                if cleaned.endswith('%'):
                    try:
                        return float(cleaned[:-1]) / 100
                    except:
                        pass
                
                try:
                    if '.' in cleaned and ',' in cleaned:
                        cleaned = cleaned.replace('.', '').replace(',', '.')
                    elif ',' in cleaned and '.' in cleaned:
                        cleaned = cleaned.replace(',', '')
                    elif ',' in cleaned and '.' not in cleaned:
                        cleaned = cleaned.replace(',', '.')
                    elif '.' in cleaned and ',' not in cleaned:
                        cleaned = cleaned.replace('.', '')
                    
                    return float(cleaned)
                except:
                    return default
            
            return default
  