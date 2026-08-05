# app/events/subscribers/notification_subscriber.py
"""
Notification Subscriber - DOCUMENT 07 REVISION 04

Sends notifications for important Events.
"""

import logging
from typing import Dict, Any, UUID
from app.events.subscribers.base_subscriber import BaseSubscriber
from app.events.models.event import Event

logger = logging.getLogger(__name__)


class NotificationSubscriber(BaseSubscriber):
    """
    Notification Subscriber - Sends notifications for Events.
    
    Handles Events that require user notifications.
    """
    
    def __init__(self, name: str = "notification_subscriber"):
        super().__init__(name)
        
        # Subscribe to relevant events
        self.subscribe_to_many([
            "execution.completed",
            "execution.failed",
            "artifact.created",
            "dataset.uploaded",
            "dataset.failed",
        ])
    
    async def handle(self, event: Event) -> None:
        """
        Handle an Event and send notification.
        """
        logger.info(f"📬 NotificationSubscriber handling: {event.event_type}")
        
        try:
            # Determine notification type
            notification_type = self._get_notification_type(event)
            
            # Prepare notification message
            message = self._prepare_notification(event)
            
            # Send notification
            await self._send_notification(event.company_id, notification_type, message)
            
        except Exception as e:
            logger.error(f"NotificationSubscriber error: {e}")
    
    def _get_notification_type(self, event: Event) -> str:
        """Get notification type from event."""
        if event.event_type == "execution.completed":
            return "execution_completed"
        elif event.event_type == "execution.failed":
            return "execution_failed"
        elif event.event_type == "artifact.created":
            return "artifact_created"
        elif event.event_type == "dataset.uploaded":
            return "dataset_uploaded"
        elif event.event_type == "dataset.failed":
            return "dataset_failed"
        return "general"
    
    def _prepare_notification(self, event: Event) -> str:
        """Prepare notification message."""
        messages = {
            "execution.completed": f"✅ Execution completed successfully (ID: {event.execution_id})",
            "execution.failed": f"❌ Execution failed (ID: {event.execution_id})",
            "artifact.created": f"📄 New AI Artifact created (ID: {event.artifact_id})",
            "dataset.uploaded": f"📤 Dataset uploaded successfully",
            "dataset.failed": f"❌ Dataset upload failed",
        }
        return messages.get(event.event_type, f"Event: {event.event_type}")
    
    async def _send_notification(self, company_id: UUID, notification_type: str, message: str) -> None:
        """Send notification."""
        logger.info(f"🔔 Notification: [{notification_type}] {message}")
        # In production, this would send email, push notification, etc.
    
    def get_subscriber_type(self) -> str:
        return "notification"