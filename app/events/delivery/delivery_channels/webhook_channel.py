# app/events/delivery/delivery_channels/webhook_channel.py
"""
Webhook Channel - DOCUMENT 07 REVISION 05

Webhook SHALL become only a delivery mechanism.
Webhook SHALL NEVER become the Event itself.
"""

from typing import Optional, Dict, Any
import httpx
import logging

from app.events.models.event import Event

logger = logging.getLogger(__name__)


class WebhookChannel:
    """
    Webhook Delivery Channel.
    
    Delivers Events to external systems via HTTP webhooks.
    Transport mechanisms SHALL be pluggable.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
    
    async def deliver(self, event: Event) -> bool:
        """
        Deliver an Event via webhook.
        
        Returns:
            bool: True if delivery was successful
        """
        # Get webhook URL from config or event metadata
        webhook_url = self._get_webhook_url(event)
        if not webhook_url:
            logger.warning(f"No webhook URL configured for event: {event.event_id}")
            return False
        
        try:
            # Prepare payload
            payload = {
                "event_id": str(event.event_id),
                "event_type": event.event_type,
                "event_version": event.event_version,
                "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                "company_id": str(event.company_id),
                "execution_id": str(event.execution_id) if event.execution_id else None,
                "artifact_id": str(event.artifact_id) if event.artifact_id else None,
                "data": event.payload,
                "metadata": event.metadata,
            }
            
            # Send webhook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    timeout=self.timeout,
                    headers={
                        "Content-Type": "application/json",
                        "X-Event-ID": str(event.event_id),
                        "X-Event-Type": event.event_type,
                        "User-Agent": "Stokonomi-AI/1.0",
                    },
                )
                
                if response.status_code in [200, 201, 202, 204]:
                    logger.info(f"Webhook delivered: {event.event_id}")
                    return True
                else:
                    logger.warning(
                        f"Webhook returned {response.status_code}: {event.event_id}"
                    )
                    return False
                    
        except httpx.TimeoutException:
            logger.error(f"Webhook timeout: {event.event_id}")
            return False
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False
    
    def _get_webhook_url(self, event: Event) -> Optional[str]:
        """Get webhook URL from event metadata or config."""
        # Check event metadata
        if event.metadata and "webhook_url" in event.metadata:
            return event.metadata["webhook_url"]
        
        # Check config
        if self.config and "default_webhook_url" in self.config:
            return self.config["default_webhook_url"]
        
        return None