# app/learning/knowledge_center.py
"""
Knowledge Center - DOCUMENT 05 - PART 02B
User interface for improving Company Learning by completing historical knowledge.
"""

from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging
import re

from sqlalchemy.orm import Session

from app.learning.learning_context import LearningContext
from app.learning.knowledge_repository import KnowledgeRepository
from app.models.learning import CompanyLearningMemory


logger = logging.getLogger(__name__)


class HistoricalCoverageAnalyzer:
    """
    Historical Coverage Analyzer - DOCUMENT 05 - PART 02B Section 4
    Evaluates historical dataset coverage by Company → Product Group → SKU → Year → Week.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_coverage(self, company_id: UUID, dataset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze historical coverage and identify missing periods.
        """
        items = dataset_data.get("items", [])
        
        # Extract all weeks from data
        available_weeks = set()
        sku_weeks = {}
        
        for item in items:
            sku = item.get("sku_code")
            week = item.get("week_start")
            if sku and week:
                available_weeks.add(week)
                if sku not in sku_weeks:
                    sku_weeks[sku] = set()
                sku_weeks[sku].add(week)
        
        # Find date range
        if not available_weeks:
            return {
                "has_data": False,
                "total_weeks": 0,
                "unique_skus": 0,
                "missing_weeks": [],
                "coverage_percentage": 0.0,
            }
        
        sorted_weeks = sorted(available_weeks)
        start_week = sorted_weeks[0]
        end_week = sorted_weeks[-1]
        
        # Generate all weeks in range
        all_weeks = self._generate_week_range(start_week, end_week)
        
        # Find missing weeks
        missing_weeks = [w for w in all_weeks if w not in available_weeks]
        
        # Calculate coverage per SKU
        sku_coverage = {}
        for sku, weeks in sku_weeks.items():
            sku_missing = [w for w in all_weeks if w not in weeks]
            sku_coverage[sku] = {
                "total_weeks": len(all_weeks),
                "available": len(weeks),
                "missing": len(sku_missing),
                "missing_weeks": sku_missing[:10],  # Limit for display
                "coverage_percentage": round(len(weeks) / len(all_weeks) * 100, 2),
            }
        
        return {
            "has_data": True,
            "start_week": start_week,
            "end_week": end_week,
            "total_weeks": len(all_weeks),
            "available_weeks": len(available_weeks),
            "missing_weeks": missing_weeks,
            "missing_count": len(missing_weeks),
            "unique_skus": len(sku_weeks),
            "coverage_percentage": round(len(available_weeks) / len(all_weeks) * 100, 2),
            "sku_coverage": sku_coverage,
        }
    
    def _generate_week_range(self, start_week: str, end_week: str) -> List[str]:
        """Generate all weeks between start and end."""
        start_year, start_week_num = self._parse_week(start_week)
        end_year, end_week_num = self._parse_week(end_week)
        
        weeks = []
        current_year = start_year
        current_week = start_week_num
        
        while current_year < end_year or (current_year == end_year and current_week <= end_week_num):
            weeks.append(f"{current_year}-W{current_week:02d}")
            current_week += 1
            if current_week > 52:
                current_week = 1
                current_year += 1
        
        return weeks
    
    def _parse_week(self, week_str: str) -> tuple:
        """Parse week string to year and week number."""
        match = re.match(r'^(\d{4})-W(\d{2})$', week_str)
        if not match:
            raise ValueError(f"Invalid week format: {week_str}")
        return int(match.group(1)), int(match.group(2))


class MissingWeekDetector:
    """
    Missing Week Detector - DOCUMENT 05 - PART 02B Section 5
    Detects missing weeks and suggests uploads.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect_missing_weeks(self, coverage: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect missing weeks and provide guidance.
        """
        if not coverage.get("has_data", False):
            return {
                "has_missing": False,
                "missing_weeks": [],
                "suggestions": [],
                "total_missing": 0,
            }
        
        missing_weeks = coverage.get("missing_weeks", [])
        
        if not missing_weeks:
            return {
                "has_missing": False,
                "missing_weeks": [],
                "suggestions": [],
                "total_missing": 0,
            }
        
        # Group missing weeks by year
        missing_by_year = {}
        for week in missing_weeks:
            year = week[:4]
            if year not in missing_by_year:
                missing_by_year[year] = []
            missing_by_year[year].append(week)
        
        # Generate suggestions
        suggestions = []
        for year, weeks in missing_by_year.items():
            suggestions.append({
                "year": year,
                "count": len(weeks),
                "weeks": weeks[:5],  # Show first 5
                "has_more": len(weeks) > 5,
                "action": f"Upload missing weeks for {year}",
            })
        
        return {
            "has_missing": True,
            "missing_weeks": missing_weeks,
            "total_missing": len(missing_weeks),
            "missing_by_year": missing_by_year,
            "suggestions": suggestions,
        }


class OptionalDatasetAnalyzer:
    """
    Optional Dataset Analyzer - DOCUMENT 05 - PART 02B Section 6
    Identifies optional datasets and their learning impact.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def analyze_optional_datasets(self, company_id: UUID) -> Dict[str, Any]:
        """
        Analyze available optional datasets.
        """
        # This would check actual data availability in a real implementation
        # For now, return placeholder structure
        
        optional_datasets = {
            "campaign_information": {
                "available": False,
                "impact": "Promotion Learning unavailable",
                "learning_layer": "Pattern Intelligence",
            },
            "supplier_information": {
                "available": False,
                "impact": "Procurement Behaviour Learning unavailable",
                "learning_layer": "Company Learning",
            },
            "inventory_levels": {
                "available": False,
                "impact": "Inventory Behaviour Learning limited",
                "learning_layer": "Company Learning",
            },
            "unit_cost": {
                "available": False,
                "impact": "Cost-based Learning limited",
                "learning_layer": "Company Learning",
            },
        }
        
        # Check availability (placeholder)
        for key in optional_datasets:
            # In real implementation, check if data exists
            pass
        
        return {
            "datasets": optional_datasets,
            "available_count": sum(1 for d in optional_datasets.values() if d["available"]),
            "total_count": len(optional_datasets),
        }


class KnowledgeCompletenessCalculator:
    """
    Knowledge Completeness Calculator - DOCUMENT 05 - PART 02B Section 8
    Calculates Knowledge Completeness Score.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
    
    def calculate(self, company_id: UUID, coverage: Dict[str, Any], optional_datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Knowledge Completeness Score.
        """
        score = 0.0
        
        # 1. Historical Coverage (max 40 points)
        coverage_pct = coverage.get("coverage_percentage", 0)
        if coverage_pct >= 90:
            score += 40
        elif coverage_pct >= 75:
            score += 30
        elif coverage_pct >= 50:
            score += 20
        elif coverage_pct >= 25:
            score += 10
        else:
            score += 5
        
        # 2. Optional Dataset Availability (max 30 points)
        available = optional_datasets.get("available_count", 0)
        total = optional_datasets.get("total_count", 0)
        if total > 0:
            optional_score = (available / total) * 30
            score += round(optional_score, 2)
        
        # 3. Validated Learning History (max 20 points)
        learnings = self.repository.get_company_learning(company_id)
        validated = len([l for l in learnings if l.is_verified])
        if validated >= 20:
            score += 20
        elif validated >= 10:
            score += 15
        elif validated >= 5:
            score += 10
        elif validated >= 1:
            score += 5
        
        # 4. Execution History (max 10 points)
        # Placeholder - actual implementation would query execution history
        score += 5
        
        return {
            "score": round(min(100, score), 2),
            "coverage_component": round(min(40, coverage_pct * 0.4), 2),
            "optional_component": round(min(30, optional_score if total > 0 else 0), 2),
            "learning_component": round(min(20, validated * 1.0), 2),
            "execution_component": 5.0,
            "level": self._get_level(score),
        }
    
    def _get_level(self, score: float) -> str:
        """Get knowledge completeness level."""
        if score >= 80:
            return "excellent"
        elif score >= 60:
            return "good"
        elif score >= 40:
            return "moderate"
        elif score >= 20:
            return "basic"
        else:
            return "limited"


class KnowledgeGuidanceService:
    """
    Knowledge Guidance Service - DOCUMENT 05 - PART 02B Section 9
    Provides guidance on missing information.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_guidance(self, company_id: UUID, coverage: Dict[str, Any], optional_datasets: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate guidance for knowledge improvement.
        """
        guidance = []
        
        # 1. Missing weeks guidance
        if coverage.get("missing_count", 0) > 0:
            guidance.append({
                "type": "missing_weeks",
                "severity": "high",
                "message": f"Missing {coverage['missing_count']} historical weeks",
                "action": "Upload missing weeks to improve historical coverage",
                "impact": "Knowledge Completeness will increase by ~15%",
            })
        
        # 2. Optional datasets guidance
        datasets = optional_datasets.get("datasets", {})
        for key, data in datasets.items():
            if not data.get("available", False):
                guidance.append({
                    "type": "missing_optional",
                    "severity": "medium",
                    "message": f"{key.replace('_', ' ').title()} not available",
                    "action": f"Add {key.replace('_', ' ')} data",
                    "impact": data.get("impact", "Learning improvement available"),
                })
        
        return {
            "guidance": guidance,
            "total_issues": len(guidance),
            "high_priority": len([g for g in guidance if g["severity"] == "high"]),
        }


class KnowledgeUpdateService:
    """
    Knowledge Update Service - DOCUMENT 05 - PART 02B Section 10
    Updates Learning without triggering analytical execution.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = KnowledgeRepository(db)
    
    def update_knowledge(self, company_id: UUID, user_id: UUID, new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update learning with new knowledge.
        NEVER triggers analytical execution.
        """
        updates = []
        
        # 1. Process new weeks
        if "weeks" in new_data:
            week_updates = self._process_weeks(company_id, user_id, new_data["weeks"])
            updates.extend(week_updates)
        
        # 2. Process optional datasets
        if "optional_datasets" in new_data:
            optional_updates = self._process_optional_datasets(
                company_id, user_id, new_data["optional_datasets"]
            )
            updates.extend(optional_updates)
        
        self.db.commit()
        
        return {
            "success": True,
            "updates": updates,
            "total_updates": len(updates),
        }
    
    def _process_weeks(self, company_id: UUID, user_id: UUID, weeks: List[Dict]) -> List[Dict]:
        """Process new week data."""
        updates = []
        for week_data in weeks:
            # Store week data in learning memory
            rule = CompanyLearningMemory(
                company_id=company_id,
                user_id=user_id,
                rule_id=f"week_data_{week_data['week']}_{datetime.now().strftime('%Y%m%d')}",
                rule_name=f"Week {week_data['week']}",
                rule_type="historical_data",
                description=f"Week data added: {week_data['week']}",
                pattern_data=week_data,
                confidence_score=0.5,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=False,
            )
            self.db.add(rule)
            updates.append({
                "type": "week_data",
                "week": week_data["week"],
                "status": "added",
            })
        
        return updates
    
    def _process_optional_datasets(self, company_id: UUID, user_id: UUID, datasets: Dict) -> List[Dict]:
        """Process optional dataset updates."""
        updates = []
        
        for key, data in datasets.items():
            rule = CompanyLearningMemory(
                company_id=company_id,
                user_id=user_id,
                rule_id=f"optional_{key}_{datetime.now().strftime('%Y%m%d')}",
                rule_name=f"Optional Dataset: {key}",
                rule_type="optional_knowledge",
                description=f"Added {key} knowledge",
                pattern_data=data,
                confidence_score=0.6,
                first_seen_at=datetime.now(),
                last_seen_at=datetime.now(),
                is_active=True,
                is_verified=False,
            )
            self.db.add(rule)
            updates.append({
                "type": "optional_dataset",
                "dataset": key,
                "status": "added",
            })
        
        return updates


class KnowledgeExplainability:
    """
    Knowledge Explainability - DOCUMENT 05 - PART 02B Section 11
    Explains every Knowledge Center update.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def explain_update(
        self,
        company_id: UUID,
        updates: List[Dict],
        completeness_before: float,
        completeness_after: float,
        confidence_before: float,
        confidence_after: float,
    ) -> Dict[str, Any]:
        """
        Generate explanation for knowledge update.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "updates": updates,
            "completeness_before": completeness_before,
            "completeness_after": completeness_after,
            "completeness_change": round(completeness_after - completeness_before, 2),
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "confidence_change": round(confidence_after - confidence_before, 3),
            "total_updates": len(updates),
            "learning_improvements": self._get_improvements(updates),
        }
    
    def _get_improvements(self, updates: List[Dict]) -> List[str]:
        """Get learning improvements from updates."""
        improvements = []
        for update in updates:
            if update.get("type") == "week_data":
                improvements.append(f"Added historical data for week {update.get('week')}")
            elif update.get("type") == "optional_dataset":
                improvements.append(f"Added {update.get('dataset')} knowledge")
        return improvements