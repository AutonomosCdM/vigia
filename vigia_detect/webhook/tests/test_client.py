"""
Tests for webhook client functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp

from ..client import WebhookClient
from ..models import WebhookEvent, EventType, WebhookResponse


class TestWebhookClient:
    """Test cases for WebhookClient."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.webhook_url = "https://api.example.com/webhook"
        self.api_key = "test-api-key"
        self.client = WebhookClient(
            webhook_url=self.webhook_url,
            api_key=self.api_key,
            timeout=5,
            retry_count=2
        )
    
    def test_client_initialization(self):
        """Test client initialization with various parameters."""
        client = WebhookClient("https://test.com/webhook")
        assert client.webhook_url == "https://test.com/webhook"
        assert client.api_key is None
        assert client.timeout == 30
        assert client.retry_count == 3
        
        client_with_params = WebhookClient(
            "https://test.com/webhook",
            api_key="key123",
            timeout=10,
            retry_count=5
        )
        assert client_with_params.api_key == "key123"
        assert client_with_params.timeout == 10
        assert client_with_params.retry_count == 5
    
    def test_prepare_headers_without_api_key(self):
        """Test header preparation without API key."""
        client = WebhookClient("https://test.com/webhook")
        headers = client._prepare_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert "Authorization" not in headers
    
    def test_prepare_headers_with_api_key(self):
        """Test header preparation with API key."""
        headers = self.client._prepare_headers()
        
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == f"Bearer {self.api_key}"
    
    @pytest.mark.asyncio
    async def test_send_async_success(self):
        """Test successful async webhook sending."""
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={"test": "data"},
            source="test"
        )
        
        # Mock successful HTTP response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "success"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await self.client.send_async(event)
            
            assert response.success is True
            assert response.status_code == 200
            assert response.data == {"status": "success"}
    
    @pytest.mark.asyncio
    async def test_send_async_http_error(self):
        """Test async webhook sending with HTTP error."""
        event = WebhookEvent(
            event_type=EventType.DETECTION_FAILED,
            timestamp=datetime.now(),
            payload={"error": "test error"},
            source="test"
        )
        
        # Mock HTTP error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.json.return_value = {"error": "Bad request"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await self.client.send_async(event)
            
            assert response.success is False
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_send_async_network_error_with_retry(self):
        """Test async webhook sending with network error and retry."""
        event = WebhookEvent(
            event_type=EventType.PATIENT_UPDATED,
            timestamp=datetime.now(),
            payload={"patient_id": "test"},
            source="test"
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Simulate network error on all attempts
            mock_post.side_effect = aiohttp.ClientError("Network error")
            
            response = await self.client.send_async(event)
            
            assert response.success is False
            assert response.status_code == 0
            assert "Network error" in response.message
            
            # Should retry according to retry_count (2)
            assert mock_post.call_count == 2
    
    @pytest.mark.asyncio
    async def test_send_batch_async(self):
        """Test batch sending of multiple events."""
        events = [
            WebhookEvent(
                event_type=EventType.DETECTION_COMPLETED,
                timestamp=datetime.now(),
                payload={"test": i},
                source="test"
            )
            for i in range(3)
        ]
        
        # Mock successful responses
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "success"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            responses = await self.client.send_batch_async(events)
            
            assert len(responses) == 3
            assert all(r.success for r in responses)
            assert mock_post.call_count == 3
    
    def test_sync_send(self):
        """Test synchronous webhook sending."""
        event = WebhookEvent(
            event_type=EventType.PROTOCOL_TRIGGERED,
            timestamp=datetime.now(),
            payload={"protocol": "test"},
            source="test"
        )
        
        # Mock the async method
        with patch.object(self.client, '_send_event') as mock_send:
            mock_send.return_value = WebhookResponse(
                success=True,
                status_code=200
            )
            
            # Mock asyncio.run to avoid actual async execution
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = WebhookResponse(
                    success=True,
                    status_code=200
                )
                
                response = self.client.send(event)
                
                assert response.success is True
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_webhook_id_generation(self):
        """Test that webhook_id is generated if not provided."""
        event = WebhookEvent(
            event_type=EventType.ANALYSIS_READY,
            timestamp=datetime.now(),
            payload={"analysis": "test"},
            source="test"
            # No webhook_id provided
        )
        
        assert event.webhook_id is None
        
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"status": "success"}
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            await self.client.send_async(event)
            
            # webhook_id should be generated
            assert event.webhook_id is not None
            assert len(event.webhook_id) > 0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={"test": "timeout"},
            source="test"
        )
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = asyncio.TimeoutError()
            
            response = await self.client.send_async(event)
            
            assert response.success is False
            assert response.message == "Request timeout"
    
    @pytest.mark.asyncio
    async def test_json_response_parsing_error(self):
        """Test handling of invalid JSON responses."""
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={"test": "json_error"},
            source="test"
        )
        
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text.return_value = "Invalid response text"
        
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.return_value.__aenter__.return_value = mock_response
            
            response = await self.client.send_async(event)
            
            assert response.success is True  # Still successful HTTP response
            assert response.data == {'raw': 'Invalid response text'}


@pytest.mark.asyncio
async def test_context_manager():
    """Test webhook client as async context manager."""
    client = WebhookClient("https://test.com/webhook")
    
    async with client as ctx_client:
        assert ctx_client.session is not None
        assert isinstance(ctx_client.session, aiohttp.ClientSession)
    
    # Session should be closed after context exit
    assert ctx_client.session.closed


@pytest.mark.integration
class TestWebhookClientIntegration:
    """Integration tests for webhook client."""
    
    @pytest.mark.asyncio
    async def test_real_webhook_endpoint(self):
        """Test against a real webhook endpoint (httpbin)."""
        client = WebhookClient("https://httpbin.org/post")
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={"integration_test": True},
            source="pytest"
        )
        
        response = await client.send_async(event)
        
        assert response.success is True
        assert response.status_code == 200
        assert "json" in response.data  # httpbin echoes the JSON payload
    
    @pytest.mark.asyncio
    async def test_authentication_failure(self):
        """Test authentication failure with real endpoint."""
        # Using httpbin's basic auth endpoint
        client = WebhookClient(
            "https://httpbin.org/bearer",
            api_key="wrong-token"
        )
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_FAILED,
            timestamp=datetime.now(),
            payload={"auth_test": True},
            source="pytest"
        )
        
        response = await client.send_async(event)
        
        assert response.success is False
        assert response.status_code == 401