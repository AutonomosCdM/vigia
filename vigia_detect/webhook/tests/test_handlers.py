"""
Tests for webhook handlers functionality.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from ..handlers import WebhookHandlers, create_default_handlers
from ..models import EventType, Severity


class TestWebhookHandlers:
    """Test cases for WebhookHandlers."""
    
    def setup_method(self):
        """Setup test fixtures."""
        # Create mock integrations
        self.mock_slack = MagicMock()
        self.mock_twilio = MagicMock()
        self.mock_db = MagicMock()
        self.mock_redis = MagicMock()
        
        # Make async methods return awaitable objects
        self.mock_slack.send_notification = AsyncMock()
        self.mock_slack.send_error_notification = AsyncMock()
        self.mock_slack.send_urgent_notification = AsyncMock()
        self.mock_slack.send_analysis_ready_notification = AsyncMock()
        
        self.mock_twilio.send_whatsapp_alert = AsyncMock()
        self.mock_twilio.send_sms_alert = AsyncMock()
        
        self.mock_redis.set = AsyncMock()
        self.mock_redis.delete_pattern = AsyncMock()
        
        self.handlers = WebhookHandlers(
            slack_notifier=self.mock_slack,
            twilio_client=self.mock_twilio,
            db_client=self.mock_db,
            redis_client=self.mock_redis
        )
    
    @pytest.mark.asyncio
    async def test_handle_detection_completed_low_risk(self):
        """Test handling low-risk detection completed events."""
        payload = {
            "patient_code": "TEST-001",
            "risk_level": "LOW",
            "detections": [
                {
                    "stage": 1,
                    "confidence": 0.8,
                    "bbox": [100, 100, 200, 200],
                    "area": 10000,
                    "severity": "low"
                }
            ],
            "total_detected": 1,
            "processing_time": 1.2
        }
        
        result = await self.handlers.handle_detection_completed(
            EventType.DETECTION_COMPLETED, payload
        )
        
        assert result["status"] == "processed"
        assert result["actions_taken"]["notifications_sent"] is False  # Low risk
        assert result["actions_taken"]["stored_in_db"] is True
        assert result["actions_taken"]["cached"] is True
        
        # Should not send urgent notifications for low risk
        self.mock_slack.send_notification.assert_not_called()
        self.mock_twilio.send_whatsapp_alert.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_detection_completed_critical_risk(self):
        """Test handling critical-risk detection completed events."""
        payload = {
            "patient_code": "TEST-002",
            "risk_level": "CRITICAL",
            "detections": [
                {
                    "stage": 4,
                    "confidence": 0.95,
                    "bbox": [100, 100, 300, 300],
                    "area": 40000,
                    "severity": "critical"
                },
                {
                    "stage": 3,
                    "confidence": 0.87,
                    "bbox": [400, 200, 600, 400],
                    "area": 40000,
                    "severity": "high"
                }
            ],
            "total_detected": 2,
            "processing_time": 2.1
        }
        
        result = await self.handlers.handle_detection_completed(
            EventType.DETECTION_COMPLETED, payload
        )
        
        assert result["status"] == "processed"
        assert result["actions_taken"]["notifications_sent"] is True  # Critical risk
        
        # Should send notifications for critical risk
        self.mock_slack.send_notification.assert_called_once()
        self.mock_twilio.send_whatsapp_alert.assert_called_once()
        
        # Check notification content
        slack_call = self.mock_slack.send_notification.call_args
        assert "CRITICAL" in slack_call[0][0]
        assert "TEST-002" in slack_call[0][0]
        
        whatsapp_call = self.mock_twilio.send_whatsapp_alert.call_args
        assert "CRITICAL" in whatsapp_call[0][0]
        assert "TEST-002" in whatsapp_call[0][0]
    
    @pytest.mark.asyncio
    async def test_handle_detection_failed(self):
        """Test handling detection failed events."""
        payload = {
            "patient_code": "TEST-003",
            "error": "Invalid image format",
            "image_path": "/path/to/image.jpg"
        }
        
        result = await self.handlers.handle_detection_failed(
            EventType.DETECTION_FAILED, payload
        )
        
        assert result["status"] == "acknowledged"
        assert result["error_logged"] is True
        assert result["notifications_sent"] is True
        
        # Should send error notification
        self.mock_slack.send_error_notification.assert_called_once()
        
        # Check error notification content
        call_args = self.mock_slack.send_error_notification.call_args
        assert call_args[1]["title"] == "Detection Failure"
        assert call_args[1]["error_message"] == "Invalid image format"
        assert call_args[1]["context"]["patient_code"] == "TEST-003"
    
    @pytest.mark.asyncio
    async def test_handle_patient_updated_status_change(self):
        """Test handling patient update events with status change."""
        payload = {
            "patient_code": "TEST-004",
            "update_type": "status_change",
            "changes": {
                "risk_level": {"old": "LOW", "new": "HIGH"},
                "status": {"old": "stable", "new": "at_risk"}
            }
        }
        
        result = await self.handlers.handle_patient_updated(
            EventType.PATIENT_UPDATED, payload
        )
        
        assert result["status"] == "processed"
        assert result["update_type"] == "status_change"
        assert result["notifications_sent"] is True  # Significant change
        
        # Should notify care team for significant changes
        self.mock_slack.send_notification.assert_called_once()
        
        # Should invalidate cache
        self.mock_redis.delete_pattern.assert_called_once_with("patient:TEST-004:*")
    
    @pytest.mark.asyncio
    async def test_handle_patient_updated_minor_change(self):
        """Test handling patient update events with minor changes."""
        payload = {
            "patient_code": "TEST-005",
            "update_type": "info_update",
            "changes": {
                "contact_info": {"phone": "new_number"}
            }
        }
        
        result = await self.handlers.handle_patient_updated(
            EventType.PATIENT_UPDATED, payload
        )
        
        assert result["status"] == "processed"
        assert result["update_type"] == "info_update"
        assert result["notifications_sent"] is False  # Minor change
        
        # Should not notify for minor changes
        self.mock_slack.send_notification.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_handle_protocol_triggered(self):
        """Test handling protocol triggered events."""
        payload = {
            "protocol_name": "Critical Pressure Injury Protocol",
            "patient_code": "TEST-006",
            "trigger_reason": "Stage 4 injury detected",
            "actions": [
                "Immediate nursing assessment",
                "Wound care specialist consultation",
                "Pressure relief mattress upgrade"
            ]
        }
        
        result = await self.handlers.handle_protocol_triggered(
            EventType.PROTOCOL_TRIGGERED, payload
        )
        
        assert result["status"] == "activated"
        assert result["protocol"] == "Critical Pressure Injury Protocol"
        assert result["tasks_created"] == 3  # One task per action
        assert result["notifications_sent"] is True
        
        # Should send urgent notifications
        self.mock_slack.send_urgent_notification.assert_called_once()
        self.mock_twilio.send_sms_alert.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_analysis_ready(self):
        """Test handling analysis ready events."""
        payload = {
            "analysis_id": "ANALYSIS-001",
            "patient_code": "TEST-007",
            "analysis_type": "trend_analysis",
            "results_url": "https://example.com/results",
            "triggers_analyses": ["tissue_assessment", "nutrition_review"]
        }
        
        result = await self.handlers.handle_analysis_ready(
            EventType.ANALYSIS_READY, payload
        )
        
        assert result["status"] == "processed"
        assert result["analysis_id"] == "ANALYSIS-001"
        assert result["notifications_sent"] is True
        assert result["triggered_workflows"] == 2
        
        # Should send analysis notification
        self.mock_slack.send_analysis_ready_notification.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handlers_without_integrations(self):
        """Test handlers work without external integrations."""
        # Create handlers with no integrations
        minimal_handlers = WebhookHandlers()
        
        payload = {
            "patient_code": "TEST-008",
            "risk_level": "HIGH",
            "detections": [],
            "total_detected": 0
        }
        
        # Should not raise exceptions
        result = await minimal_handlers.handle_detection_completed(
            EventType.DETECTION_COMPLETED, payload
        )
        
        assert result["status"] == "processed"
        assert result["actions_taken"]["notifications_sent"] is False
        assert result["actions_taken"]["stored_in_db"] is False
        assert result["actions_taken"]["cached"] is False
    
    @pytest.mark.asyncio
    async def test_error_handling_in_integrations(self):
        """Test error handling when integrations fail."""
        # Make Slack raise an exception
        self.mock_slack.send_notification.side_effect = Exception("Slack error")
        
        payload = {
            "patient_code": "TEST-009",
            "risk_level": "HIGH",
            "detections": [],
            "total_detected": 0
        }
        
        # Should handle the exception gracefully
        result = await self.handlers.handle_detection_completed(
            EventType.DETECTION_COMPLETED, payload
        )
        
        assert result["status"] == "processed"
        # Should still complete other actions despite Slack failure


class TestCreateDefaultHandlers:
    """Test the create_default_handlers factory function."""
    
    def test_create_handlers_all_disabled(self):
        """Test creating handlers with all integrations disabled."""
        handlers = create_default_handlers({
            'enable_slack': False,
            'enable_twilio': False,
            'enable_db': False,
            'enable_redis': False
        })
        
        assert handlers.slack is None
        assert handlers.twilio is None
        assert handlers.db is None
        assert handlers.redis is None
    
    def test_create_handlers_no_config(self):
        """Test creating handlers with no configuration."""
        handlers = create_default_handlers()
        
        # Should create handlers with no integrations when config is empty
        assert handlers.slack is None
        assert handlers.twilio is None
        assert handlers.db is None
        assert handlers.redis is None
    
    @patch('vigia_detect.webhook.handlers.SlackNotifier')
    def test_create_handlers_with_slack(self, mock_slack_class):
        """Test creating handlers with Slack enabled."""
        mock_slack_instance = MagicMock()
        mock_slack_class.return_value = mock_slack_instance
        
        handlers = create_default_handlers({'enable_slack': True})
        
        assert handlers.slack is mock_slack_instance
        mock_slack_class.assert_called_once()
    
    @patch('vigia_detect.webhook.handlers.SlackNotifier')
    def test_create_handlers_slack_init_error(self, mock_slack_class):
        """Test handling Slack initialization errors."""
        mock_slack_class.side_effect = Exception("Slack init error")
        
        # Should not raise exception
        handlers = create_default_handlers({'enable_slack': True})
        
        assert handlers.slack is None


@pytest.mark.integration
class TestHandlersIntegration:
    """Integration tests for webhook handlers."""
    
    @pytest.mark.asyncio
    async def test_full_detection_workflow(self):
        """Test a complete detection workflow through handlers."""
        handlers = WebhookHandlers()
        
        # Simulate detection completed
        detection_payload = {
            "patient_code": "INTEGRATION-001",
            "risk_level": "MEDIUM",
            "detections": [
                {
                    "stage": 2,
                    "confidence": 0.85,
                    "bbox": [150, 150, 250, 250],
                    "area": 10000,
                    "severity": "medium"
                }
            ],
            "total_detected": 1,
            "processing_time": 1.5
        }
        
        result = await handlers.handle_detection_completed(
            EventType.DETECTION_COMPLETED, detection_payload
        )
        
        assert result["status"] == "processed"
        
        # Simulate patient update based on detection
        update_payload = {
            "patient_code": "INTEGRATION-001",
            "update_type": "status_change",
            "changes": {"status": {"old": "stable", "new": "monitoring"}}
        }
        
        update_result = await handlers.handle_patient_updated(
            EventType.PATIENT_UPDATED, update_payload
        )
        
        assert update_result["status"] == "processed"
    
    @pytest.mark.asyncio
    async def test_concurrent_handler_execution(self):
        """Test concurrent execution of multiple handlers."""
        handlers = WebhookHandlers()
        
        # Create multiple payloads
        payloads = [
            {
                "patient_code": f"CONCURRENT-{i}",
                "risk_level": "LOW",
                "detections": [],
                "total_detected": 0
            }
            for i in range(5)
        ]
        
        # Execute handlers concurrently
        tasks = [
            handlers.handle_detection_completed(EventType.DETECTION_COMPLETED, payload)
            for payload in payloads
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        assert all(result["status"] == "processed" for result in results)