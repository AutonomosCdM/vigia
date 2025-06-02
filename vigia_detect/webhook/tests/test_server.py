"""
Tests for webhook server functionality.
"""

import pytest
import asyncio
import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from ..server import WebhookServer
from ..models import EventType, WebhookEvent


class TestWebhookServer:
    """Test cases for WebhookServer."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.server = WebhookServer(port=8080, api_key="test-key")
        self.client = TestClient(self.server.app)
    
    def test_server_initialization(self):
        """Test server initialization."""
        server = WebhookServer()
        assert server.port == 8000
        assert server.api_key is None
        assert server.app is not None
        
        server_with_auth = WebhookServer(port=9000, api_key="secret")
        assert server_with_auth.port == 9000
        assert server_with_auth.api_key == "secret"
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    def test_events_endpoint(self):
        """Test events listing endpoint."""
        # Without API key (should fail)
        response = self.client.get("/webhook/events")
        assert response.status_code == 401
        
        # With API key
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.get("/webhook/events", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "handlers" in data
        assert len(data["events"]) == 5  # All EventType values
    
    def test_webhook_endpoint_without_auth(self):
        """Test webhook endpoint without authentication."""
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "data"},
            "source": "test"
        }
        
        response = self.client.post("/webhook", json=payload)
        assert response.status_code == 401
    
    def test_webhook_endpoint_with_invalid_auth(self):
        """Test webhook endpoint with invalid authentication."""
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "data"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer wrong-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        assert response.status_code == 401
    
    def test_webhook_endpoint_with_valid_auth_no_handlers(self):
        """Test webhook endpoint with valid auth but no handlers."""
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "data"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "warning" in data["data"]
    
    def test_webhook_endpoint_with_handler(self):
        """Test webhook endpoint with registered handler."""
        # Register a handler
        @self.server.on_event(EventType.DETECTION_COMPLETED)
        async def test_handler(event_type, payload):
            return {"processed": True, "test": payload.get("test")}
        
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "handler_data"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processed_by"] == 1
        assert data["data"]["results"][0]["processed"] is True
    
    def test_webhook_endpoint_with_multiple_handlers(self):
        """Test webhook endpoint with multiple handlers for same event."""
        # Register multiple handlers
        @self.server.on_event(EventType.DETECTION_FAILED)
        async def handler1(event_type, payload):
            return {"handler": "first", "data": payload.get("error")}
        
        @self.server.on_event(EventType.DETECTION_FAILED)
        async def handler2(event_type, payload):
            return {"handler": "second", "processed": True}
        
        payload = {
            "event_type": "detection.failed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"error": "test error"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processed_by"] == 2
        assert len(data["data"]["results"]) == 2
    
    def test_webhook_endpoint_with_handler_error(self):
        """Test webhook endpoint when handler raises exception."""
        @self.server.on_event(EventType.PATIENT_UPDATED)
        async def failing_handler(event_type, payload):
            raise ValueError("Handler error")
        
        payload = {
            "event_type": "patient.updated",
            "timestamp": datetime.now().isoformat(),
            "payload": {"patient_id": "test"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["processed_by"] == 1
        assert "error" in data["data"]["results"][0]
    
    def test_webhook_endpoint_invalid_event_type(self):
        """Test webhook endpoint with invalid event type."""
        payload = {
            "event_type": "invalid.event",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "data"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 400
        assert "Invalid event type" in response.json()["detail"]
    
    def test_webhook_endpoint_missing_fields(self):
        """Test webhook endpoint with missing required fields."""
        payload = {
            "event_type": "detection.completed",
            # Missing timestamp, payload, source
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_register_handler_programmatically(self):
        """Test registering handlers programmatically."""
        async def test_handler(event_type, payload):
            return {"programmatic": True}
        
        self.server.register_handler(EventType.PROTOCOL_TRIGGERED, test_handler)
        
        assert EventType.PROTOCOL_TRIGGERED in self.server.event_handlers
        assert len(self.server.event_handlers[EventType.PROTOCOL_TRIGGERED]) == 1
    
    def test_on_event_decorator(self):
        """Test the on_event decorator."""
        @self.server.on_event(EventType.ANALYSIS_READY)
        async def decorated_handler(event_type, payload):
            return {"decorated": True}
        
        assert EventType.ANALYSIS_READY in self.server.event_handlers
        assert len(self.server.event_handlers[EventType.ANALYSIS_READY]) == 1
        
        # The decorator should return the original function
        assert decorated_handler.__name__ == "decorated_handler"
    
    def test_sync_handler_support(self):
        """Test that synchronous handlers are supported."""
        @self.server.on_event(EventType.DETECTION_COMPLETED)
        def sync_handler(event_type, payload):
            return {"sync": True, "type": str(event_type)}
        
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "sync"},
            "source": "test"
        }
        
        headers = {"Authorization": "Bearer test-key"}
        response = self.client.post("/webhook", json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["results"][0]["sync"] is True


class TestWebhookServerWithoutAuth:
    """Test webhook server without authentication."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.server = WebhookServer()  # No API key
        self.client = TestClient(self.server.app)
    
    def test_webhook_endpoint_no_auth_required(self):
        """Test webhook endpoint when no authentication is configured."""
        @self.server.on_event(EventType.DETECTION_COMPLETED)
        async def handler(event_type, payload):
            return {"no_auth": True}
        
        payload = {
            "event_type": "detection.completed",
            "timestamp": datetime.now().isoformat(),
            "payload": {"test": "no_auth"},
            "source": "test"
        }
        
        # No authorization header needed
        response = self.client.post("/webhook", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["results"][0]["no_auth"] is True
    
    def test_events_endpoint_no_auth_required(self):
        """Test events endpoint when no authentication is configured."""
        # No authorization header needed
        response = self.client.get("/webhook/events")
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "handlers" in data


@pytest.mark.integration
class TestWebhookServerIntegration:
    """Integration tests for webhook server."""
    
    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self):
        """Test server can start and stop properly."""
        server = WebhookServer(port=8081)
        
        # Test that we can get the FastAPI app
        app = server.get_app()
        assert app is not None
        
        # Test with TestClient
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_webhook_requests(self):
        """Test handling concurrent webhook requests."""
        server = WebhookServer()
        client = TestClient(server.app)
        
        request_count = 0
        
        @server.on_event(EventType.DETECTION_COMPLETED)
        async def concurrent_handler(event_type, payload):
            nonlocal request_count
            request_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return {"request_id": payload.get("id")}
        
        # Send multiple concurrent requests
        import threading
        responses = []
        
        def send_request(request_id):
            payload = {
                "event_type": "detection.completed",
                "timestamp": datetime.now().isoformat(),
                "payload": {"id": request_id},
                "source": "test"
            }
            resp = client.post("/webhook", json=payload)
            responses.append(resp)
        
        threads = []
        for i in range(5):
            thread = threading.Thread(target=send_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(responses) == 5
        assert all(r.status_code == 200 for r in responses)
        assert request_count == 5