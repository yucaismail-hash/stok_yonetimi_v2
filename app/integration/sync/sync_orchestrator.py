# app/integration/sync/sync_orchestrator.py
"""
Sync Orchestrator - DOCUMENT 07 APP-029 / REVISION 06

Synchronization coordinates workflows.
It does not perform synchronization itself.

Synchronization modes:
- Manual
- Scheduled
- Event Driven

shall all use the same orchestrator.
"""

from typing import Optional, Dict, Any, Callable, List
from uuid import UUID
import asyncio
import logging

from app.integration.adapters.base_adapter import BaseAdapter
from app.integration.pipelines.import_pipeline import ImportPipeline
from app.integration.pipelines.export_pipeline import ExportPipeline
from app.integration.errors.error_handler import ErrorHandler

logger = logging.getLogger(__name__)


class SyncOrchestrator:
    """
    Sync Orchestrator - Coordinates synchronization workflows.
    
    All sync modes (Manual, Scheduled, Event Driven) SHALL use this orchestrator.
    """
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self._sync_handlers: Dict[str, Callable] = {}
    
    def register_sync_handler(self, name: str, handler: Callable) -> None:
        """Register a sync handler."""
        self._sync_handlers[name] = handler
        logger.info(f"Registered sync handler: {name}")
    
    async def sync(
        self,
        adapter: BaseAdapter,
        sync_type: str = "manual",
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute synchronization.
        
        Args:
            adapter: Integration adapter
            sync_type: manual, scheduled, event_driven
            config: Sync configuration
        
        Returns:
            Sync result
        """
        logger.info(f"Starting sync: {sync_type}")
        
        try:
            # Get sync handler
            handler = self._sync_handlers.get(sync_type)
            if not handler:
                raise ValueError(f"Unknown sync type: {sync_type}")
            
            # Execute handler
            result = await handler(adapter, config or {})
            
            logger.info(f"Sync completed: {sync_type}")
            return result
            
        except Exception as e:
            return self.error_handler.handle(e, {"sync_type": sync_type})
    
    async def manual_sync(
        self,
        adapter: BaseAdapter,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute manual synchronization.
        """
        return await self.sync(adapter, "manual", config)
    
    async def scheduled_sync(
        self,
        adapter: BaseAdapter,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute scheduled synchronization.
        """
        return await self.sync(adapter, "scheduled", config)
    
    async def event_driven_sync(
        self,
        adapter: BaseAdapter,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute event-driven synchronization.
        """
        return await self.sync(adapter, "event_driven", config)
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status."""
        return {
            "registered_handlers": list(self._sync_handlers.keys()),
            "active": True,
        }