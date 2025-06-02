"""
Pytest configuration and fixtures for webhook tests.
"""

import pytest
import asyncio
import os
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def test_api_key():
    """Test API key for webhook authentication."""
    return os.environ.get("WEBHOOK_TEST_API_KEY", "test-webhook-api-key")


@pytest.fixture
def integration_api_key():
    """Integration test API key for webhook authentication."""
    return os.environ.get("WEBHOOK_INTEGRATION_API_KEY", "integration-test-webhook-key")


@pytest.fixture
def test_webhook_url():
    """Test webhook URL."""
    return os.environ.get("WEBHOOK_TEST_URL", "https://api.example.com/webhook")


@pytest.fixture
def test_webhook_port():
    """Test webhook server port."""
    return int(os.environ.get("WEBHOOK_TEST_PORT", "8090"))


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_slack_notifier():
    """Mock Slack notifier for testing."""
    mock = MagicMock()
    mock.send_notification = AsyncMock()
    mock.send_error_notification = AsyncMock()
    mock.send_urgent_notification = AsyncMock()
    mock.send_analysis_ready_notification = AsyncMock()
    return mock


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock = MagicMock()
    mock.send_whatsapp_alert = AsyncMock()
    mock.send_sms_alert = AsyncMock()
    return mock


@pytest.fixture
def mock_db_client():
    """Mock database client for testing."""
    mock = MagicMock()
    mock.save_detection = AsyncMock()
    mock.update_patient = AsyncMock()
    mock.log_protocol_activation = AsyncMock()
    return mock


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock = MagicMock()
    mock.set = AsyncMock()
    mock.get = AsyncMock()
    mock.delete = AsyncMock()
    mock.delete_pattern = AsyncMock()
    return mock


@pytest.fixture
def sample_detection_payload():
    """Sample detection payload for testing."""
    return {
        "patient_code": "TEST-001",
        "risk_level": "HIGH",
        "image_path": "/test/image.jpg",
        "detections": [
            {
                "stage": 3,
                "confidence": 0.89,
                "bbox": [100, 100, 200, 200],
                "area": 10000,
                "severity": "high"
            }
        ],
        "total_detected": 1,
        "processing_time": 1.5
    }


@pytest.fixture
def sample_patient_update_payload():
    """Sample patient update payload for testing."""
    return {
        "patient_code": "TEST-002",
        "update_type": "status_change",
        "changes": {
            "risk_level": {"old": "LOW", "new": "HIGH"},
            "status": {"old": "stable", "new": "at_risk"}
        },
        "reason": "Multiple injuries detected"
    }


@pytest.fixture
def sample_protocol_payload():
    """Sample protocol trigger payload for testing."""
    return {
        "protocol_name": "High Risk Pressure Injury Protocol",
        "patient_code": "TEST-003",
        "trigger_reason": "Stage 3+ injury with high confidence",
        "actions": [
            "Immediate assessment",
            "Specialist consultation",
            "Enhanced monitoring"
        ],
        "priority": "HIGH"
    }


# Pytest markers for different test categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (may be slower)"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast)"
    )
    config.addinivalue_line(
        "markers", "async: marks tests as async tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names and content."""
    for item in items:
        # Mark tests with "integration" in name as integration tests
        if "integration" in item.name.lower() or (item.cls and "Integration" in str(item.cls)):
            item.add_marker("integration")
        
        # Mark async tests
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker("async")
        
        # Mark remaining tests as unit tests
        existing_markers = [mark.name for mark in item.iter_markers()]
        if not any(mark in ["integration", "async"] for mark in existing_markers):
            item.add_marker("unit")