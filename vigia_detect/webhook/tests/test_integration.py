"""
End-to-end integration tests for the webhook system.
"""

import pytest
import asyncio
import json
import time
import threading
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from ..client import WebhookClient
from ..server import WebhookServer
from ..handlers import create_default_handlers
from ..models import WebhookEvent, EventType


@pytest.mark.integration
class TestWebhookSystemIntegration:
    """End-to-end integration tests for the complete webhook system."""
    
    def setup_method(self):
        """Setup integration test environment."""
        self.test_port = 8090
        self.test_url = f"http://localhost:{self.test_port}/webhook"
        self.test_api_key = "integration-test-key"
        
        # Store received events for verification
        self.received_events = []
        
        # Setup server
        self.server = WebhookServer(port=self.test_port, api_key=self.test_api_key)
        self.handlers = create_default_handlers({
            'enable_slack': False,
            'enable_twilio': False,
            'enable_db': False,
            'enable_redis': False
        })
        
        # Register test handlers
        self._register_test_handlers()
        
        # Start server in background thread
        self.server_thread = None
        self.start_test_server()
    
    def teardown_method(self):
        """Cleanup after integration tests."""
        self.stop_test_server()
    
    def _register_test_handlers(self):
        """Register handlers that store events for verification."""
        
        @self.server.on_event(EventType.DETECTION_COMPLETED)
        async def handle_detection(event_type, payload):
            event_data = {
                'type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            self.received_events.append(event_data)
            return await self.handlers.handle_detection_completed(event_type, payload)
        
        @self.server.on_event(EventType.DETECTION_FAILED)
        async def handle_failure(event_type, payload):
            event_data = {
                'type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            self.received_events.append(event_data)
            return await self.handlers.handle_detection_failed(event_type, payload)
        
        @self.server.on_event(EventType.PATIENT_UPDATED)
        async def handle_update(event_type, payload):
            event_data = {
                'type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            self.received_events.append(event_data)
            return await self.handlers.handle_patient_updated(event_type, payload)
        
        @self.server.on_event(EventType.PROTOCOL_TRIGGERED)
        async def handle_protocol(event_type, payload):
            event_data = {
                'type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            self.received_events.append(event_data)
            return await self.handlers.handle_protocol_triggered(event_type, payload)
        
        @self.server.on_event(EventType.ANALYSIS_READY)
        async def handle_analysis(event_type, payload):
            event_data = {
                'type': event_type,
                'payload': payload,
                'timestamp': datetime.now().isoformat()
            }
            self.received_events.append(event_data)
            return await self.handlers.handle_analysis_ready(event_type, payload)
    
    def start_test_server(self):
        """Start the webhook server in a background thread."""
        def run_server():
            import uvicorn
            uvicorn.run(
                self.server.app,
                host="127.0.0.1",
                port=self.test_port,
                log_level="warning"
            )
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
    
    def stop_test_server(self):
        """Stop the webhook server."""
        # Server will stop when thread exits due to daemon=True
        pass
    
    @pytest.mark.asyncio
    async def test_complete_detection_workflow(self):
        """Test a complete detection workflow from client to handlers."""
        client = WebhookClient(self.test_url, api_key=self.test_api_key)
        
        # Create detection event
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={
                "patient_code": "INTEGRATION-001",
                "risk_level": "HIGH",
                "image_path": "/test/integration.jpg",
                "detections": [
                    {
                        "stage": 3,
                        "confidence": 0.92,
                        "bbox": [150, 150, 300, 300],
                        "area": 22500,
                        "severity": "high"
                    }
                ],
                "total_detected": 1,
                "processing_time": 2.1
            },
            source="integration_test"
        )
        
        # Send event
        response = await client.send_async(event)
        
        # Verify response
        assert response.success is True
        assert response.status_code == 200
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify event was received and processed
        assert len(self.received_events) == 1
        received = self.received_events[0]
        assert received['type'] == EventType.DETECTION_COMPLETED
        assert received['payload']['patient_code'] == "INTEGRATION-001"
        assert received['payload']['risk_level'] == "HIGH"
    
    @pytest.mark.asyncio
    async def test_multiple_event_types(self):
        """Test sending multiple different event types."""
        client = WebhookClient(self.test_url, api_key=self.test_api_key)
        
        events = [
            WebhookEvent(
                event_type=EventType.DETECTION_COMPLETED,
                timestamp=datetime.now(),
                payload={
                    "patient_code": "MULTI-001",
                    "risk_level": "MEDIUM",
                    "detections": [],
                    "total_detected": 0
                },
                source="integration_test"
            ),
            WebhookEvent(
                event_type=EventType.PATIENT_UPDATED,
                timestamp=datetime.now(),
                payload={
                    "patient_code": "MULTI-001",
                    "update_type": "status_change",
                    "changes": {"status": {"old": "stable", "new": "monitoring"}}
                },
                source="integration_test"
            ),
            WebhookEvent(
                event_type=EventType.PROTOCOL_TRIGGERED,
                timestamp=datetime.now(),
                payload={
                    "protocol_name": "Monitoring Protocol",
                    "patient_code": "MULTI-001",
                    "trigger_reason": "Status change detected",
                    "actions": ["Increase monitoring frequency"]
                },
                source="integration_test"
            )
        ]
        
        # Send all events
        responses = await client.send_batch_async(events)
        
        # Verify all responses
        assert len(responses) == 3
        assert all(r.success for r in responses)
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Verify all events were received
        assert len(self.received_events) == 3
        
        # Verify event types
        received_types = [event['type'] for event in self.received_events]
        assert EventType.DETECTION_COMPLETED in received_types
        assert EventType.PATIENT_UPDATED in received_types
        assert EventType.PROTOCOL_TRIGGERED in received_types
    
    @pytest.mark.asyncio
    async def test_authentication_failures(self):
        """Test authentication failure scenarios."""
        # Client with wrong API key
        wrong_client = WebhookClient(self.test_url, api_key="wrong-key")
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_FAILED,
            timestamp=datetime.now(),
            payload={"error": "auth test"},
            source="integration_test"
        )
        
        response = await wrong_client.send_async(event)
        
        # Should fail authentication
        assert response.success is False
        assert response.status_code == 401
        
        # Should not be processed
        await asyncio.sleep(0.5)
        assert len(self.received_events) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent webhook requests."""
        client = WebhookClient(self.test_url, api_key=self.test_api_key)
        
        # Create multiple events for concurrent sending
        events = [
            WebhookEvent(
                event_type=EventType.DETECTION_COMPLETED,
                timestamp=datetime.now(),
                payload={
                    "patient_code": f"CONCURRENT-{i}",
                    "risk_level": "LOW",
                    "detections": [],
                    "total_detected": 0
                },
                source="integration_test"
            )
            for i in range(10)
        ]
        
        # Send all events concurrently
        tasks = [client.send_async(event) for event in events]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(responses) == 10
        assert all(r.success for r in responses)
        
        # Wait for all processing
        await asyncio.sleep(2)
        
        # All should be received
        assert len(self.received_events) == 10
        
        # Verify all different patient codes were processed
        patient_codes = [event['payload']['patient_code'] for event in self.received_events]
        expected_codes = [f"CONCURRENT-{i}" for i in range(10)]
        assert set(patient_codes) == set(expected_codes)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_handlers(self):
        """Test error handling when handlers raise exceptions."""
        # Add a handler that always fails
        @self.server.on_event(EventType.ANALYSIS_READY)
        async def failing_handler(event_type, payload):
            raise ValueError("Simulated handler failure")
        
        client = WebhookClient(self.test_url, api_key=self.test_api_key)
        
        event = WebhookEvent(
            event_type=EventType.ANALYSIS_READY,
            timestamp=datetime.now(),
            payload={
                "analysis_id": "ERROR-TEST",
                "patient_code": "ERROR-PATIENT",
                "analysis_type": "error_test"
            },
            source="integration_test"
        )
        
        response = await client.send_async(event)
        
        # Request should still succeed even if handler fails
        assert response.success is True
        assert response.status_code == 200
        
        # Handler error should be captured in response
        assert "error" in str(response.data).lower()
    
    def test_server_health_check(self):
        """Test server health check endpoint."""
        import requests
        
        health_url = f"http://localhost:{self.test_port}/health"
        response = requests.get(health_url)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_events_endpoint(self):
        """Test events listing endpoint."""
        import requests
        
        events_url = f"http://localhost:{self.test_port}/webhook/events"
        
        # Without auth
        response = requests.get(events_url)
        assert response.status_code == 401
        
        # With auth
        headers = {"Authorization": f"Bearer {self.test_api_key}"}
        response = requests.get(events_url, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "events" in data
        assert "handlers" in data
        assert len(data["events"]) == 5  # All event types


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world webhook usage scenarios."""
    
    @pytest.mark.asyncio
    async def test_medical_emergency_workflow(self):
        """Test a complete medical emergency workflow."""
        # This would test a realistic scenario:
        # 1. Critical detection triggers webhook
        # 2. Protocol activation follows
        # 3. Patient status updates
        # 4. Analysis completion
        
        # For brevity, this is a simplified test
        client = WebhookClient("https://httpbin.org/post")  # Public test endpoint
        
        # Simulate critical detection
        critical_event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload={
                "patient_code": "EMERGENCY-001",
                "risk_level": "CRITICAL",
                "detections": [
                    {
                        "stage": 4,
                        "confidence": 0.98,
                        "bbox": [100, 100, 400, 400],
                        "area": 90000,
                        "severity": "critical"
                    }
                ]
            },
            source="vigia_emergency_test"
        )
        
        response = await client.send_async(critical_event)
        
        # Should successfully send to external endpoint
        assert response.success is True
        assert response.status_code == 200
        
        # httpbin echoes the data back
        assert "vigia_emergency_test" in str(response.data)
        assert "EMERGENCY-001" in str(response.data)
    
    @pytest.mark.asyncio
    async def test_network_resilience(self):
        """Test webhook resilience to network issues."""
        # Test with non-existent endpoint
        client = WebhookClient(
            "http://localhost:99999/webhook",  # Should fail
            retry_count=2,
            timeout=1
        )
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_FAILED,
            timestamp=datetime.now(),
            payload={"error": "network test"},
            source="resilience_test"
        )
        
        response = await client.send_async(event)
        
        # Should fail gracefully
        assert response.success is False
        assert response.status_code == 0  # Network error
        assert "error" in response.message.lower() or "timeout" in response.message.lower()