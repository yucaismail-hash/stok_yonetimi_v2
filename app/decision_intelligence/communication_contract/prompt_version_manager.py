# app/decision_intelligence/communication_contract/prompt_version_manager.py
"""
Prompt Version Manager - DOCUMENT 06 - PART 05
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PromptVersionManager:
    """
    Prompt Version Manager - CP-005
    
    Manages prompt versions and lifecycle.
    """
    
    def __init__(self):
        self._versions: Dict[str, Dict[str, Any]] = {}
        self._current_version = "1.0.0"
        self._load_versions()
    
    def _load_versions(self):
        """Load prompt versions."""
        self._versions = {
            "1.0.0": {
                "version": "1.0.0",
                "created_at": "2026-01-01",
                "status": "active",
                "features": ["executive_summary", "findings", "recommendations"],
            },
            "1.1.0": {
                "version": "1.1.0",
                "created_at": "2026-02-01",
                "status": "active",
                "features": ["executive_summary", "findings", "risks", "opportunities", "recommendations"],
            },
            "2.0.0": {
                "version": "2.0.0",
                "created_at": "2026-03-01",
                "status": "active",
                "features": ["all_analysis_types", "structured_narrative", "explainability"],
            },
        }
        self._current_version = "2.0.0"
    
    def get_current_version(self) -> str:
        """Get current prompt version."""
        return self._current_version
    
    def get_version_info(self, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get version information."""
        return self._versions.get(version or self._current_version)
    
    def get_features(self, version: Optional[str] = None) -> list:
        """Get features for a version."""
        info = self.get_version_info(version)
        return info.get("features", []) if info else []
    
    def supports_feature(self, feature: str, version: Optional[str] = None) -> bool:
        """Check if feature is supported."""
        features = self.get_features(version)
        return feature in features
    
    def list_versions(self) -> list:
        """List all prompt versions."""
        return list(self._versions.keys())