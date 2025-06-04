"""
Shared test fixtures for the Vigia project.
Provides consistent test setup across all modules.
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator, List
from unittest.mock import Mock, MagicMock
import json
from datetime import datetime

# Test data constants
SAMPLE_PATIENT_CODES = [
    "CD-2025-001",
    "AB-2024-999", 
    "XY-2025-123"
]

SAMPLE_IMAGE_METADATA = {
    "width": 1920,
    "height": 1080,
    "channels": 3,
    "format": "JPEG"
}

SAMPLE_DETECTION_RESULTS = {
    "detections": [
        {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.85,
            "grade": 2,
            "location": "sacro"
        }
    ],
    "confidence_scores": [0.85],
    "processing_time": 1.23
}


@pytest.fixture
def temp_directory() -> Generator[Path, None, None]:
    """Create a temporary directory for testing"""
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_image_path(temp_directory: Path) -> Path:
    """Create a sample image file for testing"""
    image_path = temp_directory / "sample_image.jpg"
    # Create a minimal valid image file (1x1 pixel)
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    with open(image_path, 'wb') as f:
        f.write(image_data)
    
    return image_path


@pytest.fixture
def sample_patient_code() -> str:
    """Provide a sample patient code"""
    return SAMPLE_PATIENT_CODES[0]


@pytest.fixture
def invalid_patient_codes() -> List[str]:
    """Provide invalid patient codes for testing"""
    return [
        "",
        "INVALID",
        "CD-25-001",  # Wrong year format
        "C-2025-001",  # Wrong prefix format
        "CD-2025-1",   # Wrong number format
        "CD-2025-ABCD"  # Non-numeric number
    ]


@pytest.fixture
def mock_supabase_client() -> Mock:
    """Mock Supabase client for testing"""
    mock_client = Mock()
    mock_client.table.return_value.select.return_value.execute.return_value = Mock(
        data=[{"id": 1, "patient_code": "CD-2025-001"}]
    )
    mock_client.table.return_value.insert.return_value.execute.return_value = Mock(
        data=[{"id": 1}]
    )
    return mock_client


@pytest.fixture
def mock_twilio_client() -> Mock:
    """Mock Twilio client for testing"""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "test_message_sid"
    mock_client.messages.create.return_value = mock_message
    return mock_client


@pytest.fixture
def mock_slack_client() -> Mock:
    """Mock Slack client for testing"""
    mock_client = Mock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1234567890.123456"}
    mock_client.auth_test.return_value = {"ok": True, "user": "test_bot"}
    return mock_client


@pytest.fixture
def mock_detector() -> Mock:
    """Mock LPP detector for testing"""
    mock_detector = Mock()
    mock_detector.detect.return_value = SAMPLE_DETECTION_RESULTS
    mock_detector.confidence_threshold = 0.25
    return mock_detector


@pytest.fixture
def mock_preprocessor() -> Mock:
    """Mock image preprocessor for testing"""
    mock_preprocessor = Mock()
    mock_preprocessor.preprocess.return_value = "processed_image_data"
    mock_preprocessor.get_original_size.return_value = (1920, 1080)
    mock_preprocessor.get_applied_steps.return_value = ["resize", "normalize"]
    return mock_preprocessor


@pytest.fixture
def sample_detection_payload() -> Dict[str, Any]:
    """Sample detection payload for testing"""
    return {
        "patient_code": SAMPLE_PATIENT_CODES[0],
        "image_path": "/test/path/image.jpg",
        "detection_results": SAMPLE_DETECTION_RESULTS,
        "timestamp": datetime.now().isoformat(),
        "processing_id": "test-123"
    }


@pytest.fixture
def mock_redis_client() -> Mock:
    """Mock Redis client for testing"""
    mock_client = Mock()
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.health_check.return_value = {
        "redis": True,
        "cache": True,
        "vector_search": True
    }
    return mock_client


@pytest.fixture
def mock_webhook_client() -> Mock:
    """Mock webhook client for testing"""
    mock_client = Mock()
    mock_client.send_async.return_value = {
        "success": True,
        "webhook_id": "test-webhook-123",
        "status_code": 200
    }
    return mock_client


@pytest.fixture
def sample_settings() -> Dict[str, Any]:
    """Sample settings for testing"""
    return {
        "environment": "test",
        "debug": True,
        "log_level": "DEBUG",
        "supabase_url": "https://test.supabase.co",
        "supabase_key": "test_key",
        "twilio_account_sid": "test_sid",
        "twilio_auth_token": "test_token",
        "slack_bot_token": "xoxb-test-token",
        "model_confidence": 0.25,
        "use_mock_yolo": True
    }


@pytest.fixture
def test_config_file(temp_directory: Path) -> Path:
    """Create a test configuration file"""
    config_data = {
        "test_setting": "test_value",
        "database": {
            "url": "test://localhost",
            "timeout": 30
        }
    }
    
    config_path = temp_directory / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    return config_path


@pytest.fixture
def mock_health_checker() -> Mock:
    """Mock health checker for testing"""
    mock_checker = Mock()
    mock_checker.check_services.return_value = {
        "database": {"status": "healthy", "response_time": 0.1},
        "redis": {"status": "healthy", "response_time": 0.05},
        "external_apis": {"status": "healthy", "response_time": 0.3}
    }
    return mock_checker


class TestDataFactory:
    """Factory for creating test data objects"""
    
    @staticmethod
    def create_detection_result(grade: int = 2, confidence: float = 0.85) -> Dict[str, Any]:
        """Create a test detection result"""
        return {
            "bbox": [100, 100, 200, 200],
            "confidence": confidence,
            "grade": grade,
            "location": "sacro",
            "severity": "medium" if grade >= 2 else "low"
        }
    
    @staticmethod
    def create_patient_data(patient_code: str = None) -> Dict[str, Any]:
        """Create test patient data"""
        return {
            "patient_code": patient_code or SAMPLE_PATIENT_CODES[0],
            "age": 65,
            "gender": "M",
            "admission_date": "2025-01-01",
            "room_number": "101"
        }
    
    @staticmethod
    def create_processing_result(success: bool = True, **kwargs) -> Dict[str, Any]:
        """Create test processing result"""
        base_result = {
            "success": success,
            "processing_id": "test-123",
            "timestamp": datetime.now().isoformat(),
            "processor_version": "test_v1.0"
        }
        
        if success:
            base_result.update({
                "results": SAMPLE_DETECTION_RESULTS,
                "processing_time_seconds": 1.23
            })
        else:
            base_result.update({
                "error": kwargs.get("error", "Test error"),
                "error_code": kwargs.get("error_code", "TEST_ERROR")
            })
        
        base_result.update(kwargs)
        return base_result


@pytest.fixture
def test_data_factory() -> TestDataFactory:
    """Provide test data factory"""
    return TestDataFactory()


# Utility functions for tests
def assert_valid_patient_code(patient_code: str) -> None:
    """Assert that a patient code is valid"""
    parts = patient_code.split('-')
    assert len(parts) == 3, f"Invalid patient code format: {patient_code}"
    assert len(parts[0]) == 2 and parts[0].isalpha(), "Invalid prefix"
    assert len(parts[1]) == 4 and parts[1].isdigit(), "Invalid year"
    assert len(parts[2]) == 3 and parts[2].isdigit(), "Invalid number"


def assert_detection_result_structure(result: Dict[str, Any]) -> None:
    """Assert that a detection result has the expected structure"""
    required_fields = ["bbox", "confidence", "grade"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    assert isinstance(result["bbox"], list), "bbox must be a list"
    assert len(result["bbox"]) == 4, "bbox must have 4 coordinates"
    assert 0 <= result["confidence"] <= 1, "confidence must be between 0 and 1"
    assert isinstance(result["grade"], int), "grade must be an integer"
    assert 0 <= result["grade"] <= 4, "grade must be between 0 and 4"