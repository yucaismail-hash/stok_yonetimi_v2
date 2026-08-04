# app/services/dataset/dataset_validation_engine.py
"""
Dataset Validation Engine
DOCUMENT 02 - Section 12: Dataset Validation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetValidationResult
from app.models.company import User

logger = logging.getLogger(__name__)


class DatasetValidationEngine:
    """
    Dataset Validasyon Motoru.
    
    Validasyonlar:
    - Yapı kontrolü
    - Zorunlu alanlar
    - Veri tipleri
    - Tarih tutarlılığı
    - Hafta sürekliliği
    - Tekrar eden kayıtlar
    - İş kuralları
    """
    
    # Zorunlu alanlar
    REQUIRED_FIELDS = [
        "sku_code",
        "sku_name",
        "week_start",
        "demand",
    ]
    
    # İzin verilen veri tipleri
    FIELD_TYPES = {
        "sku_code": str,
        "sku_name": str,
        "week_start": str,  # ISO format: "2026-W01"
        "demand": (int, float),
        "price": (int, float),
        "stock": (int, float),
        "lead_time": int,
        "supplier_code": str,
    }
    
    # İş kuralları
    BUSINESS_RULES = {
        "demand_non_negative": lambda x: x.get("demand", 0) >= 0,
        "price_non_negative": lambda x: x.get("price", 0) >= 0,
        "stock_non_negative": lambda x: x.get("stock", 0) >= 0,
        "lead_time_positive": lambda x: x.get("lead_time", 0) > 0,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate(self, dataset: Dataset, data: Dict[str, Any]) -> DatasetValidationResult:
        """
        Dataset'i validate et.
        DOCUMENT 02 - Section 12: Validation Wizard
        """
        result = DatasetValidationResult(
            dataset_id=dataset.id,
            errors=[],
            warnings=[],
            requires_user_approval=False,
        )
        
        # 1. Yapı kontrolü
        structure_errors = self._validate_structure(data)
        if structure_errors:
            result.errors.extend(structure_errors)
        
        # 2. Zorunlu alanlar
        required_errors = self._validate_required_fields(data)
        if required_errors:
            result.errors.extend(required_errors)
        
        # 3. Veri tipleri
        type_errors = self._validate_data_types(data)
        if type_errors:
            result.errors.extend(type_errors)
        
        # 4. Tarih tutarlılığı
        date_errors, date_warnings = self._validate_dates(data)
        if date_errors:
            result.errors.extend(date_errors)
        if date_warnings:
            result.warnings.extend(date_warnings)
        
        # 5. Hafta sürekliliği
        continuity_warnings = self._validate_week_continuity(data)
        if continuity_warnings:
            result.warnings.extend(continuity_warnings)
        
        # 6. Tekrar eden kayıtlar
        duplicate_errors = self._validate_duplicates(data)
        if duplicate_errors:
            result.errors.extend(duplicate_errors)
        
        # 7. İş kuralları
        business_errors = self._validate_business_rules(data)
        if business_errors:
            result.errors.extend(business_errors)
        
        # 8. Veri yeterliliği (DOCUMENT 02 - Section 14)
        sufficiency_warnings = self._validate_data_sufficiency(data)
        if sufficiency_warnings:
            result.warnings.extend(sufficiency_warnings)
        
        # Sonuç
        result.is_valid = len(result.errors) == 0
        
        # Validasyon sonucunu kaydet
        self.db.add(result)
        self.db.commit()
        
        logger.info(f"Dataset {dataset.id} validation completed: {'✅' if result.is_valid else '❌'}")
        
        return result
    
    def _validate_structure(self, data: Dict[str, Any]) -> List[str]:
        """Yapı kontrolü."""
        errors = []
        
        if not isinstance(data, dict):
            errors.append("Data must be a dictionary")
            return errors
        
        if "items" not in data:
            errors.append("Missing 'items' field")
            return errors
        
        if not isinstance(data["items"], list):
            errors.append("'items' must be a list")
            return errors
        
        if len(data["items"]) == 0:
            errors.append("'items' cannot be empty")
            return errors
        
        # Her öğenin dict olup olmadığını kontrol et
        for i, item in enumerate(data["items"]):
            if not isinstance(item, dict):
                errors.append(f"Item {i} must be a dictionary")
        
        return errors
    
    def _validate_required_fields(self, data: Dict[str, Any]) -> List[str]:
        """Zorunlu alan kontrolü."""
        errors = []
        
        for i, item in enumerate(data.get("items", [])):
            for field in self.REQUIRED_FIELDS:
                if field not in item or item[field] is None or item[field] == "":
                    errors.append(f"Item {i}: Missing required field '{field}'")
        
        return errors
    
    def _validate_data_types(self, data: Dict[str, Any]) -> List[str]:
        """Veri tipi kontrolü."""
        errors = []
        
        for i, item in enumerate(data.get("items", [])):
            for field, expected_type in self.FIELD_TYPES.items():
                if field in item and item[field] is not None:
                    if not isinstance(item[field], expected_type):
                        errors.append(
                            f"Item {i}: Field '{field}' must be {expected_type.__name__}, "
                            f"got {type(item[field]).__name__}"
                        )
        
        return errors
    
    def _validate_dates(self, data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Tarih tutarlılığı kontrolü."""
        errors = []
        warnings = []
        
        week_pattern = re.compile(r'^(\d{4})-W(\d{2})$')
        dates = []
        
        for i, item in enumerate(data.get("items", [])):
            week_start = item.get("week_start")
            if not week_start:
                continue
            
            # Format kontrolü (YYYY-WW)
            match = week_pattern.match(week_start)
            if not match:
                errors.append(f"Item {i}: Invalid week format '{week_start}'. Expected: YYYY-WW")
                continue
            
            year = int(match.group(1))
            week = int(match.group(2))
            
            if week < 1 or week > 53:
                errors.append(f"Item {i}: Invalid week number {week}. Must be 1-53")
                continue
            
            # ISO hafta yılının geçerli olup olmadığını kontrol et
            try:
                # 1 Ocak'ı al
                jan1 = datetime(year, 1, 1)
                # Haftanın ilk gününü hesapla
                days_to_thursday = (3 - jan1.weekday()) % 7
                first_monday = jan1 + timedelta(days=days_to_thursday - 3)
                # Hafta başlangıcını hesapla
                week_start_date = first_monday + timedelta(weeks=week - 1)
                dates.append(week_start_date)
            except Exception as e:
                errors.append(f"Item {i}: Invalid date calculation for week {week_start}: {str(e)}")
        
        # Tarih aralığı kontrolü
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            
            # 52 haftadan az mı?
            if (max_date - min_date).days < 364:  # 52 * 7
                warnings.append(f"Data covers only {(max_date - min_date).days // 7} weeks. Minimum 52 weeks recommended.")
        
        return errors, warnings
    
    def _validate_week_continuity(self, data: Dict[str, Any]) -> List[str]:
        """Hafta sürekliliği kontrolü."""
        warnings = []
        
        weeks = set()
        for item in data.get("items", []):
            week_start = item.get("week_start")
            if week_start:
                weeks.add(week_start)
        
        if not weeks:
            return warnings
        
        sorted_weeks = sorted(weeks)
        
        # Eksik hafta var mı?
        if len(sorted_weeks) >= 2:
            for i in range(len(sorted_weeks) - 1):
                current = self._week_to_date(sorted_weeks[i])
                next_week = self._week_to_date(sorted_weeks[i + 1])
                
                if current and next_week:
                    week_diff = (next_week - current).days // 7
                    if week_diff > 1:
                        warnings.append(
                            f"Missing weeks between {sorted_weeks[i]} and {sorted_weeks[i + 1]} "
                            f"({week_diff - 1} weeks missing)"
                        )
        
        return warnings
    
    def _validate_duplicates(self, data: Dict[str, Any]) -> List[str]:
        """Tekrar eden kayıt kontrolü."""
        errors = []
        
        seen = set()
        for i, item in enumerate(data.get("items", [])):
            key = f"{item.get('sku_code')}_{item.get('week_start')}"
            if key in seen:
                errors.append(f"Item {i}: Duplicate record for '{key}'")
            else:
                seen.add(key)
        
        return errors
    
    def _validate_business_rules(self, data: Dict[str, Any]) -> List[str]:
        """İş kuralları kontrolü."""
        errors = []
        
        for i, item in enumerate(data.get("items", [])):
            for rule_name, rule_func in self.BUSINESS_RULES.items():
                try:
                    if not rule_func(item):
                        errors.append(f"Item {i}: Business rule '{rule_name}' failed")
                except Exception as e:
                    errors.append(f"Item {i}: Business rule '{rule_name}' error: {str(e)}")
        
        return errors
    
    def _validate_data_sufficiency(self, data: Dict[str, Any]) -> List[str]:
        """Veri yeterliliği kontrolü."""
        warnings = []
        
        # SKU sayısı kontrolü
        skus = set()
        for item in data.get("items", []):
            sku_code = item.get("sku_code")
            if sku_code:
                skus.add(sku_code)
        
        if len(skus) < 3:
            warnings.append(f"Only {len(skus)} SKUs found. Minimum 3 SKUs recommended for meaningful analysis.")
        
        # Hafta sayısı kontrolü
        weeks = set()
        for item in data.get("items", []):
            week_start = item.get("week_start")
            if week_start:
                weeks.add(week_start)
        
        if len(weeks) < 26:
            warnings.append(f"Only {len(weeks)} weeks found. Minimum 26 weeks recommended for meaningful analysis.")
        
        return warnings
    
    def _week_to_date(self, week_str: str) -> Optional[datetime]:
        """Week string'ini date'e çevir."""
        try:
            match = re.match(r'^(\d{4})-W(\d{2})$', week_str)
            if not match:
                return None
            
            year = int(match.group(1))
            week = int(match.group(2))
            
            jan1 = datetime(year, 1, 1)
            days_to_thursday = (3 - jan1.weekday()) % 7
            first_monday = jan1 + timedelta(days=days_to_thursday - 3)
            
            return first_monday + timedelta(weeks=week - 1)
        except:
            return None