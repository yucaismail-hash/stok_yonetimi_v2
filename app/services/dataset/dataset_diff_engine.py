# app/services/dataset/dataset_diff_engine.py
"""
Dataset Diff Engine
DOCUMENT 02 - Section 11: Dataset Diff
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
import hashlib
import json
import logging

from sqlalchemy.orm import Session

from app.models.dataset import Dataset, DatasetDiffResult

logger = logging.getLogger(__name__)


class DatasetDiffEngine:
    """
    Dataset Diff Motoru.
    
    İki dataset arasındaki farkları tespit eder:
    - Yeni SKU
    - Silinen SKU
    - Değiştirilen SKU
    - Değiştirilen Tarihsel Değerler
    - Eksik Periyotlar
    - Tekrar Eden Kayıtlar
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def diff(self, new_data: Dict[str, Any], old_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Diff işlemini gerçekleştir.
        """
        result = {
            "new_skus": [],
            "removed_skus": [],
            "modified_skus": [],
            "modified_historical_values": [],
            "missing_periods": [],
            "duplicate_records": [],
            "summary": {
                "total_added": 0,
                "total_removed": 0,
                "total_modified": 0,
                "total_historical_modifications": 0,
            }
        }
        
        if not old_data:
            # Yeni dataset, tüm SKU'lar yeni
            skus = self._extract_skus(new_data)
            result["new_skus"] = skus
            result["summary"]["total_added"] = len(skus)
            return result
        
        # SKU'ları çıkar
        old_skus = set(self._extract_skus(old_data))
        new_skus = set(self._extract_skus(new_data))
        
        # 1. Yeni SKU'lar
        result["new_skus"] = list(new_skus - old_skus)
        result["summary"]["total_added"] = len(result["new_skus"])
        
        # 2. Silinen SKU'lar
        result["removed_skus"] = list(old_skus - new_skus)
        result["summary"]["total_removed"] = len(result["removed_skus"])
        
        # 3. Değiştirilen SKU'lar
        common_skus = old_skus & new_skus
        
        old_data_by_sku = self._group_by_sku(old_data)
        new_data_by_sku = self._group_by_sku(new_data)
        
        modified_skus = []
        for sku in common_skus:
            old_sku_data = old_data_by_sku.get(sku, [])
            new_sku_data = new_data_by_sku.get(sku, [])
            
            if self._is_sku_modified(old_sku_data, new_sku_data):
                modified_skus.append(sku)
                
                # 4. Tarihsel değer değişiklikleri
                historical_changes = self._find_historical_changes(old_sku_data, new_sku_data)
                if historical_changes:
                    result["modified_historical_values"].append({
                        "sku": sku,
                        "changes": historical_changes
                    })
        
        result["modified_skus"] = modified_skus
        result["summary"]["total_modified"] = len(modified_skus)
        result["summary"]["total_historical_modifications"] = len(result["modified_historical_values"])
        
        # 5. Eksik periyotlar
        result["missing_periods"] = self._find_missing_periods(new_data)
        
        # 6. Tekrar eden kayıtlar
        result["duplicate_records"] = self._find_duplicates(new_data)
        
        # Diff hash
        result["diff_hash"] = self._calculate_diff_hash(result)
        
        return result
    
    def _extract_skus(self, data: Dict[str, Any]) -> List[str]:
        """Dataset'ten SKU listesini çıkar."""
        skus = []
        for item in data.get("items", []):
            sku = item.get("sku_code")
            if sku:
                skus.append(str(sku))
        return list(set(skus))
    
    def _group_by_sku(self, data: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Data'yı SKU bazında grupla."""
        grouped = defaultdict(list)
        for item in data.get("items", []):
            sku = str(item.get("sku_code", ""))
            if sku:
                grouped[sku].append(item)
        return dict(grouped)
    
    def _is_sku_modified(self, old_data: List[Dict], new_data: List[Dict]) -> bool:
        """SKU'nun değişip değişmediğini kontrol et."""
        # Farklı sayıda kayıt varsa değişmiştir
        if len(old_data) != len(new_data):
            return True
        
        # Verileri karşılaştır
        old_sorted = sorted(old_data, key=lambda x: x.get("week_start", ""))
        new_sorted = sorted(new_data, key=lambda x: x.get("week_start", ""))
        
        for old_item, new_item in zip(old_sorted, new_sorted):
            # Week start aynı değilse değişmiştir
            if old_item.get("week_start") != new_item.get("week_start"):
                return True
            
            # Demand değeri değişmiş mi?
            old_demand = old_item.get("demand", 0)
            new_demand = new_item.get("demand", 0)
            
            if old_demand != new_demand:
                return True
        
        return False
    
    def _find_historical_changes(self, old_data: List[Dict], new_data: List[Dict]) -> List[Dict]:
        """Tarihsel değer değişikliklerini bul."""
        changes = []
        
        old_map = {item.get("week_start", ""): item for item in old_data}
        new_map = {item.get("week_start", ""): item for item in new_data}
        
        # Ortak haftaları bul
        common_weeks = set(old_map.keys()) & set(new_map.keys())
        
        for week in common_weeks:
            old_item = old_map[week]
            new_item = new_map[week]
            
            # Demand değişikliği
            old_demand = old_item.get("demand", 0)
            new_demand = new_item.get("demand", 0)
            
            if old_demand != new_demand:
                # Değişim yüzdesi
                if old_demand > 0:
                    change_percent = ((new_demand - old_demand) / old_demand) * 100
                else:
                    change_percent = 100 if new_demand > 0 else 0
                
                changes.append({
                    "week": week,
                    "old_value": old_demand,
                    "new_value": new_demand,
                    "change_percent": round(change_percent, 2),
                    "requires_approval": abs(change_percent) > 20  # %20'den fazla değişim onay gerektirir
                })
        
        return changes
    
    def _find_missing_periods(self, data: Dict[str, Any]) -> List[Dict]:
        """Eksik periyotları bul."""
        missing = []
        
        weeks_per_sku = defaultdict(set)
        for item in data.get("items", []):
            sku = str(item.get("sku_code", ""))
            week = item.get("week_start", "")
            if sku and week:
                weeks_per_sku[sku].add(week)
        
        # Her SKU için eksik haftaları bul
        for sku, weeks in weeks_per_sku.items():
            if len(weeks) < 2:
                continue
            
            sorted_weeks = sorted(weeks)
            for i in range(len(sorted_weeks) - 1):
                current = sorted_weeks[i]
                next_week = sorted_weeks[i + 1]
                
                # Hafta farkını hesapla
                week_diff = self._week_difference(current, next_week)
                if week_diff > 1:
                    missing.append({
                        "sku": sku,
                        "missing_weeks": week_diff - 1,
                        "from": current,
                        "to": next_week
                    })
        
        return missing
    
    def _find_duplicates(self, data: Dict[str, Any]) -> List[Dict]:
        """Tekrar eden kayıtları bul."""
        duplicates = []
        
        seen = {}
        for i, item in enumerate(data.get("items", [])):
            sku = str(item.get("sku_code", ""))
            week = item.get("week_start", "")
            key = f"{sku}_{week}"
            
            if key in seen:
                duplicates.append({
                    "sku": sku,
                    "week": week,
                    "first_index": seen[key],
                    "second_index": i
                })
            else:
                seen[key] = i
        
        return duplicates
    
    def _week_difference(self, week1: str, week2: str) -> int:
        """İki hafta arasındaki farkı hesapla."""
        import re
        from datetime import datetime, timedelta
        
        def week_to_date(week_str: str) -> datetime:
            match = re.match(r'^(\d{4})-W(\d{2})$', week_str)
            if not match:
                return datetime.now()
            
            year = int(match.group(1))
            week = int(match.group(2))
            
            jan1 = datetime(year, 1, 1)
            days_to_thursday = (3 - jan1.weekday()) % 7
            first_monday = jan1 + timedelta(days=days_to_thursday - 3)
            
            return first_monday + timedelta(weeks=week - 1)
        
        try:
            d1 = week_to_date(week1)
            d2 = week_to_date(week2)
            return abs((d2 - d1).days // 7)
        except:
            return 0
    
    def _calculate_diff_hash(self, diff_result: Dict[str, Any]) -> str:
        """Diff sonucunun hash'ini hesapla."""
        # Hash'ten summary'yi çıkar
        hash_data = {
            "new_skus": sorted(diff_result["new_skus"]),
            "removed_skus": sorted(diff_result["removed_skus"]),
            "modified_skus": sorted(diff_result["modified_skus"]),
            "summary": diff_result["summary"]
        }
        
        json_str = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()[:16]
    
    def save_diff_result(self, dataset_id: int, diff_result: Dict[str, Any]) -> DatasetDiffResult:
        """Diff sonucunu kaydet."""
        result = DatasetDiffResult(
            dataset_id=dataset_id,
            previous_dataset_id=diff_result.get("previous_dataset_id"),
            new_skus=diff_result.get("new_skus", []),
            removed_skus=diff_result.get("removed_skus", []),
            modified_skus=diff_result.get("modified_skus", []),
            modified_historical_values=diff_result.get("modified_historical_values", []),
            missing_periods=diff_result.get("missing_periods", []),
            duplicate_records=diff_result.get("duplicate_records", []),
            total_changes=(
                len(diff_result.get("new_skus", [])) +
                len(diff_result.get("removed_skus", [])) +
                len(diff_result.get("modified_skus", []))
            ),
            requires_approval=self._check_requires_approval(diff_result),
        )
        
        self.db.add(result)
        self.db.commit()
        
        logger.info(f"✅ Diff result saved for dataset {dataset_id}")
        
        return result
    
    def _check_requires_approval(self, diff_result: Dict[str, Any]) -> bool:
        """Onay gerekip gerekmediğini kontrol et."""
        # Büyük değişiklikler onay gerektirir
        if len(diff_result.get("removed_skus", [])) > 0:
            return True
        
        # Tarihsel değişiklikler %20'den fazla ise onay gerektirir
        for change in diff_result.get("modified_historical_values", []):
            for item in change.get("changes", []):
                if item.get("requires_approval", False):
                    return True
        
        return False