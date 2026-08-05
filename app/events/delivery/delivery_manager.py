# app/events/delivery/delivery_manager.py
"""
Delivery Manager - DOCUMENT 07 APP-039

Delivery SHALL support:
- Immediate Delivery
- Scheduled Retry
- Failure Tracking
- Duplicate Prevention

Future transport mechanisms SHALL reuse this policy.
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
import asyncio
import logging

from app.events.models.event import Event, EventStatus
from app.events.delivery.retry_policy import RetryPolicy
from app.events.delivery.delivery_channels.webhook_channel import WebhookChannel
from app.events.repository.event_repository import EventRepository

logger = logging.getLogger(__name__)


class DeliveryManager:
    """
    Delivery Manager - Coordinates Event delivery.
    
    Delivery Manager SHALL remain independent from transport technology.
    Transport mechanisms SHALL be pluggable.
    """
    
    def __init__(self):
        self.repository = EventRepository()
        self.retry_policy = RetryPolicy()
        self.channels = {}
        self._register_default_channels()
    
    def _register_default_channels(self):
        """Register default delivery channels."""
        self.register_channel("webhook", WebhookChannel())
    
    def register_channel(self, name: str, channel) -> None:
        """Register a delivery channel."""
        self.channels[name] = channel
        logger.info(f"Registered delivery channel: {name}")
    
    async def enqueue(self, event: Event) -> None:
        """Enqueue an Event for delivery."""
        logger.info(f"📬 Event queued for delivery: {event.event_id}")
        
        # Start delivery
        await self.deliver(event)
    
    async def deliver(self, event: Event) -> None:
        """
        Deliver an Event through registered channels.
        """
        # Update status
        event = event.with_status(EventStatus.PUBLISHED)
        await self.repository.update(event)
        
        # Deliver through each channel
        for channel_name, channel in self.channels.items():
            try:
                success = await channel.deliver(event)
                
                if success:
                    event = event.with_status(EventStatus.DELIVERED)
                    await self.repository.update(event)
                    logger.info(f"✅ Event delivered via {channel_name}: {event.event_id}")
                else:
                    await self._handle_delivery_failure(event, channel_name)
                    
            except Exception as e:
                logger.error(f"Delivery error via {channel_name}: {e}")
                await self._handle_delivery_failure(event, channel_name)
    
    async def _handle_delivery_failure(self, event: Event, channel_name: str) -> None:
        """Handle delivery failure with retry policy."""
        # Get delivery status
        status = await self.repository.get_delivery_status(event.event_id)
        retry_count = status.get("retry_count", 0) if status else 0
        
        # Check if retry is allowed
        if self.retry_policy.should_retry(retry_count):
            # Schedule retry
            delay = self.retry_policy.get_delay(retry_count)
            logger.info(f"🔄 Retrying event {event.event_id} (attempt {retry_count + 1}) in {delay}s")
            
            # Update status
            event = event.with_status(EventStatus.RETRYING)
            await self.repository.update(event)
            
            # Schedule retry
            asyncio.create_task(self._retry_delivery(event, channel_name, retry_count + 1, delay))
        else:
            # Max retries exceeded
            event = event.with_status(EventStatus.FAILED)
            await self.repository.update(event)
            logger.error(f"❌ Event delivery failed after {retry_count} retries: {event.event_id}")
    
    async def _retry_delivery(self, event: Event, channel_name: str, attempt: int, delay: int) -> None:
        """Retry delivery after delay."""
        await asyncio.sleep(delay)
        
        channel = self.channels.get(channel_name)
        if not channel:
            logger.error(f"Channel not found: {channel_name}")
            return
        
        try:
            success = await channel.deliver(event)
            
            if success:
                event = event.with_status(EventStatus.DELIVERED)
                await self.repository.update(event)
                logger.info(f"✅ Event delivered on retry {attempt}: {event.event_id}")
            else:
                await self._handle_delivery_failure(event, channel_name)
                
        except Exception as e:
            logger.error(f"Retry delivery error: {e}")
            await self._handle_delivery_failure(event, channel_name)