# app/services/normalization_engine.py
"""
Smart Import Engine - Akıllı Veri Standardizasyonu
"""

import re
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models import NormalizationRule

logger = logging.getLogger(__name__)


class NormalizationEngine:
    """
    Akıllı Veri Standardizasyonu Motoru
    - Otomatik düzeltme
    - Smart Suggestion
    - Güven eşiği kontrolü
    """
    
    def __init__(self, db: Session, user_id: int, upload_id: str):
        self.db = db
        self.user_id = user_id
        self.upload_id = upload_id
        self.rules = self._load_rules()
    
    def _load_rules(self) -> List[NormalizationRule]:
        """Aktif normalizasyon kurallarını yükle"""
        return self.db.query(NormalizationRule).filter(
            NormalizationRule.is_active == True
        ).all()
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tüm veriyi normalize et
        """
        normalized = {}
        changes = []
        suggestions = []
        errors = []
        
        for sheet_name, rows in data.items():
            if not rows:
                normalized[sheet_name] = []
                continue
            
            normalized[sheet_name] = []
            for row in rows:
                new_row = dict(row)
                for key, value in row.items():
                    if isinstance(value, str):
                        original = value
                        new_value, confidence, suggestion = self._normalize_value(value, key)
                        
                        if new_value != original:
                            changes.append({
                                'sheet': sheet_name,
                                'column': key,
                                'original': original,
                                'new': new_value,
                                'confidence': confidence
                            })
                            
                            # Eğer güven eşiğinin altındaysa suggestion olarak ekle
                            if confidence < 0.8 and suggestion:
                                suggestions.append({
                                    'sheet': sheet_name,
                                    'column': key,
                                    'original': original,
                                    'suggestion': suggestion,
                                    'confidence': confidence
                                })
                            
                            new_row[key] = new_value
                        elif value and confidence < 0.8:
                            # Düzeltilemedi ama yorumlanamadı
                            errors.append({
                                'sheet': sheet_name,
                                'column': key,
                                'value': value,
                                'message': 'Yorumlanamadı, manuel düzeltme gerekli'
                            })
                
                normalized[sheet_name].append(new_row)
        
        return {
            'normalized_data': normalized,
            'changes': changes,
            'suggestions': suggestions,
            'errors': errors,
            'total_changes': len(changes),
            'total_suggestions': len(suggestions),
            'total_errors': len(errors)
        }
    
    def _normalize_value(self, value: str, column: str = None) -> tuple:
        """
        Tek bir değeri normalize et
        Returns: (new_value, confidence, suggestion)
        """
        result = value
        confidence = 1.0
        suggestion = None
        
        # 1. Baş ve sondaki boşlukları temizle
        result = result.strip()
        
        # 2. Çoklu boşlukları tek boşluğa çevir
        if '  ' in result:
            result = re.sub(r'\s+', ' ', result)
            confidence *= 0.95
        
        # 3. TAB karakterlerini temizle
        if '\t' in result:
            result = result.replace('\t', ' ')
            confidence *= 0.95
        
        # 4. Sayısal dönüşümler
        # 10.000 → 10000
        if re.match(r'^[\d,.]{1,}([\.,][\d]{3}){1,}$', result):
            original = result
            result = result.replace('.', '').replace(',', '')
            confidence = 0.96
            suggestion = f"{original} → {result}"
        
        # 10,000.00 → 10000
        elif re.match(r'^\d{1,3}(,\d{3})*(\.\d{2})?$', result):
            original = result
            result = result.replace(',', '').replace('.', '')
            confidence = 0.96
            suggestion = f"{original} → {result}"
        
        # 10000,00 → 10000.00
        elif re.match(r'^\d+,\d{2}$', result):
            original = result
            result = result.replace(',', '.')
            confidence = 0.96
            suggestion = f"{original} → {result}"
        
        # 5. Büyük harfe çevir (ürün kodları için)
        if column and ('kod' in column.lower() or 'code' in column.lower()):
            if not result.isdigit() and len(result) < 30:
                original = result
                result = result.upper()
                if result != original:
                    confidence *= 0.98
        
        # 6. Yüzde değerleri
        if column and ('oran' in column.lower() or 'rate' in column.lower() or 'yüzde' in column.lower()):
            if result.endswith('%'):
                original = result
                result = result.rstrip('%')
                confidence *= 0.97
                suggestion = f"{original} → {result}"
        
        # 7. Özel karakterleri temizle (güvenli olmayanlar)
        # (Opsiyonel)
        
        return result, confidence, suggestion
    
    def apply_suggestion(self, original: str, suggestion: str) -> str:
        """Kullanıcının seçtiği suggestion'ı uygula"""
        # Suggestion string'inden yeni değeri çıkar
        if ' → ' in suggestion:
            parts = suggestion.split(' → ')
            if len(parts) == 2:
                return parts[1]
        return original


def get_normalization_engine(db: Session, user_id: int, upload_id: str) -> NormalizationEngine:
    return NormalizationEngine(db, user_id, upload_id)