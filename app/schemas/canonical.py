# app/schemas/canonical.py
"""
Canonical Schema Mapping - Excel kolon adlarını internal field'lara eşler.
"""

import re
from typing import Dict, List, Optional

# Excel'deki Türkçe kolon adları -> canonical field adları
CANONICAL_MAP = {
    # Temel_Veriler
    "Ürün Kodu": "product_code",
    "Ürün Adı": "description",
    "Ürün Grubu": "group",
    "Dönem Başı Stok": "initial_stock",
    "Tedarik Süresi (Gün)": "lead_time_days",
    "Sipariş Parti Büyüklüğü": "eoq",
    "Birim Maliyet (TL)": "unit_cost",
    "Stok Tutma Oranı (%)": "holding_rate",
    "Stok Tükenme Maliyeti": "shortage_cost",
    "Talep Geçmişi (W1-Wn)": "historical_demand",
    # Tedarikciler
    "Tedarikçi Kodu": "supplier_id",
    "Tedarikçi Adı": "supplier_name",
    "Tedarikçi Faktörü": "factor",
    "Zamanında Teslim Oranı (%)": "ontime_rate",
    "Ortalama Teslim Süresi (Gün)": "lt_mean",
    "Teslim Süresi Standart Sapması": "lt_std",
    # Malzeme_Tedarikciler
    "Tedarik Payı (%)": "share",
    "Açık Sipariş": "open_qty",
    "Planlanan Teslim Tarihi": "planned_due",
}

# Reverse mapping (internal -> display)
REVERSE_CANONICAL_MAP = {v: k for k, v in CANONICAL_MAP.items()}

# Hangi kolonların hangi veri tipinde olması gerektiği (canonical field bazında)
FIELD_TYPES = {
    "product_code": "string",
    "description": "string",
    "group": "string",
    "initial_stock": "float",
    "lead_time_days": "float",
    "eoq": "float",
    "unit_cost": "float",
    "holding_rate": "percentage",
    "shortage_cost": "float",
    "historical_demand": "list",
    "supplier_id": "string",
    "supplier_name": "string",
    "factor": "float",
    "ontime_rate": "percentage",
    "lt_mean": "float",
    "lt_std": "float",
    "share": "percentage",
    "open_qty": "float",
    "planned_due": "date",
}

# Hangi alanların hangi sheet'te olması gerektiği (sheet bazında)
SHEET_FIELDS = {
    "Temel_Veriler": [
        "product_code",
        "description",
        "group",
        "initial_stock",
        "lead_time_days",
        "eoq",
        "unit_cost",
        "holding_rate",
        "shortage_cost",
        "historical_demand",
    ],
    "Tedarikciler": [
        "supplier_id",
        "supplier_name",
        "factor",
        "ontime_rate",
        "lt_mean",
        "lt_std",
    ],
    "Malzeme_Tedarikciler": [
        "product_code",
        "supplier_id",
        "share",
        "open_qty",
        "planned_due",
    ],
}

# Kritik alanlar (dataset oluşturmak için zorunlu, coverage %100 olmalı)
CRITICAL_FIELDS = {
    "Temel_Veriler": ["product_code", "lead_time_days"],
    "Tedarikciler": ["supplier_id", "ontime_rate"],
    "Malzeme_Tedarikciler": ["product_code", "supplier_id", "share"],
}

# Opsiyonel alanlar (coverage kontrolü yapılmayacak, ama geçersiz değer kontrolü yapılacak)
OPTIONAL_FIELDS = {
    "Temel_Veriler": [
        "holding_rate",      # Stok Tutma Oranı - opsiyonel
        "shortage_cost",     # Stok Tükenme Maliyeti - opsiyonel
        "eoq",               # Sipariş Parti Büyüklüğü - opsiyonel
        "unit_cost",         # Birim Maliyet - opsiyonel
        "group",             # Ürün Grubu - opsiyonel
    ],
    "Tedarikciler": [
        "factor",            # Tedarikçi Faktörü - opsiyonel
        "lt_mean",           # Ortalama Teslim Süresi - opsiyonel
        "lt_std",            # Teslim Süresi Standart Sapması - opsiyonel
        "supplier_name",     # Tedarikçi Adı - opsiyonel
    ],
    "Malzeme_Tedarikciler": [
        "open_qty",          # Açık Sipariş - opsiyonel
        "planned_due",       # Planlanan Teslim Tarihi - opsiyonel
    ],
}


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_canonical_field(excel_column: str) -> str:
    """Excel kolon adını canonical field'a çevirir."""
    if not excel_column:
        return excel_column
    return CANONICAL_MAP.get(excel_column, excel_column)


def get_excel_column(canonical_field: str) -> str:
    """Canonical field'ı Excel kolon adına çevirir."""
    if not canonical_field:
        return canonical_field
    return REVERSE_CANONICAL_MAP.get(canonical_field, canonical_field)


def normalize_column_name(column_name: str) -> str:
    """
    Kolon adını normalize eder (küçük harf, Türkçe karakterler, boşluklar)
    """
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