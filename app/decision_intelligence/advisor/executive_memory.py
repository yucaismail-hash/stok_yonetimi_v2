# app/decision_intelligence/advisor/executive_memory.py
"""
Executive Memory - DOCUMENT 06 - PART 04
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class ExecutiveMemory:
    """
    Executive Memory - EA-003
    
    Maintains historical Executive Advisor Reports.
    """
    
    def __init__(self):
        self._reports: Dict[str, Dict[str, Any]] = {}
        self._company_reports: Dict[str, List[str]] = {}
    
    def add_report(self, company_id: str, report: Dict[str, Any]) -> str:
        """Add a report to executive memory."""
        report_id = report.get("report_id", str(uuid4()))
        
        if company_id not in self._company_reports:
            self._company_reports[company_id] = []
        
        self._reports[report_id] = {
            "report_id": report_id,
            "company_id": company_id,
            "report": report,
            "created_at": datetime.now().isoformat(),
        }
        
        if report_id not in self._company_reports[company_id]:
            self._company_reports[company_id].append(report_id)
        
        logger.info(f"✅ Executive Memory updated: {company_id}")
        return report_id
    
    def get_reports(self, company_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get historical reports for a company."""
        report_ids = self._company_reports.get(company_id, [])
        result = []
        
        for rid in report_ids[-limit:]:
            report = self._reports.get(rid)
            if report:
                result.append(report)
        
        return sorted(result, key=lambda x: x.get("created_at", ""), reverse=True)
    
    def get_latest(self, company_id: str) -> Optional[Dict[str, Any]]:
        """Get latest report for a company."""
        reports = self.get_reports(company_id, 1)
        return reports[0] if reports else None
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report by ID."""
        return self._reports.get(report_id)