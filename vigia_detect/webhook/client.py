"""
Webhook client for sending detection results to external systems.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid

from .models import WebhookEvent, WebhookResponse, EventType, DetectionPayload


logger = logging.getLogger(__name__)


class WebhookClient:
    """Client for sending webhook notifications."""
    
    def __init__(self, webhook_url: str, api_key: Optional[str] = None, 
                 timeout: int = 30, retry_count: int = 3):
        """
        Initialize webhook client.
        
        Args:
            webhook_url: Target webhook endpoint
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            retry_count: Number of retry attempts on failure
        """
        self.webhook_url = webhook_url
        self.api_key = api_key
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare request headers."""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Vigia-Webhook-Client/1.0'
        }
        
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
            
        return headers
        
    async def send_detection(self, detection_payload: DetectionPayload) -> WebhookResponse:
        """
        Send detection results via webhook.
        
        Args:
            detection_payload: Detection results to send
            
        Returns:
            WebhookResponse with status
        """
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            payload=detection_payload,
            webhook_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            source="vigia_detect"
        )
        
        return await self._send_event(event)
    
    async def send_async(self, event: WebhookEvent) -> WebhookResponse:
        """
        Send a webhook event asynchronously.
        
        Args:
            event: Webhook event to send
            
        Returns:
            WebhookResponse with status
        """
        # Ensure webhook_id is set
        if not event.webhook_id:
            event.webhook_id = str(uuid.uuid4())
        return await self._send_event(event)
    
    def send(self, event: WebhookEvent) -> WebhookResponse:
        """
        Send a webhook event synchronously.
        
        Args:
            event: Webhook event to send
            
        Returns:
            WebhookResponse with status
        """
        # Ensure webhook_id is set
        if not event.webhook_id:
            event.webhook_id = str(uuid.uuid4())
        
        # Check if there's already an event loop running
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            future = asyncio.create_task(self._send_event(event))
            # This won't work in sync context, so we need different approach
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                return executor.submit(asyncio.run, self._send_event(event)).result()
        except RuntimeError:
            # No event loop running, create one
            return asyncio.run(self._send_event(event))
    
    async def send_batch_async(self, events: List[WebhookEvent]) -> List[WebhookResponse]:
        """
        Send multiple webhook events asynchronously.
        
        Args:
            events: List of webhook events
            
        Returns:
            List of responses
        """
        # Ensure all events have webhook_id
        for event in events:
            if not event.webhook_id:
                event.webhook_id = str(uuid.uuid4())
        return await self.batch_send(events)
        
    async def _send_event(self, event: WebhookEvent) -> WebhookResponse:
        """
        Send webhook event with retry logic.
        
        Args:
            event: Webhook event to send
            
        Returns:
            WebhookResponse
        """
        if not self.session:
            self.session = aiohttp.ClientSession()
            
        headers = self._prepare_headers()
        data = json.dumps(event.to_dict())
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Sending webhook event {event.webhook_id} (attempt {attempt + 1})")
                
                async with self.session.post(
                    self.webhook_url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    response_data = None
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_data = {'raw': await response.text()}
                        
                    if response.status < 300:
                        logger.info(f"Webhook sent successfully: {event.webhook_id}")
                        return WebhookResponse(
                            success=True,
                            status_code=response.status,
                            data=response_data
                        )
                    else:
                        logger.warning(f"Webhook failed with status {response.status}")
                        
                        if attempt == self.retry_count - 1:
                            return WebhookResponse(
                                success=False,
                                status_code=response.status,
                                message=f"Failed after {self.retry_count} attempts",
                                data=response_data
                            )
                            
            except asyncio.TimeoutError:
                logger.error(f"Webhook timeout on attempt {attempt + 1}")
                if attempt == self.retry_count - 1:
                    return WebhookResponse(
                        success=False,
                        status_code=0,
                        message="Request timeout"
                    )
                    
            except Exception as e:
                logger.error(f"Webhook error on attempt {attempt + 1}: {str(e)}")
                if attempt == self.retry_count - 1:
                    return WebhookResponse(
                        success=False,
                        status_code=0,
                        message=str(e)
                    )
                    
            # Wait before retry
            if attempt < self.retry_count - 1:
                await asyncio.sleep(2 ** attempt)
                
        return WebhookResponse(
            success=False,
            status_code=0,
            message="Max retries exceeded"
        )
        
    async def batch_send(self, events: List[WebhookEvent]) -> List[WebhookResponse]:
        """
        Send multiple webhook events concurrently.
        
        Args:
            events: List of webhook events
            
        Returns:
            List of responses
        """
        tasks = [self._send_event(event) for event in events]
        return await asyncio.gather(*tasks)


class SyncWebhookClient:
    """Synchronous wrapper for WebhookClient."""
    
    def __init__(self, webhook_url: str, api_key: Optional[str] = None,
                 timeout: int = 30, retry_count: int = 3):
        self.async_client = WebhookClient(webhook_url, api_key, timeout, retry_count)
        
    def send_detection(self, detection_payload: DetectionPayload) -> WebhookResponse:
        """Send detection synchronously."""
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(
                self._send_async(detection_payload)
            )
        finally:
            loop.close()
            
    async def _send_async(self, detection_payload: DetectionPayload) -> WebhookResponse:
        """Helper for async send."""
        async with self.async_client as client:
            return await client.send_detection(detection_payload)