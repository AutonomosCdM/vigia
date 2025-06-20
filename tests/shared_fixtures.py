"""
Shared test fixtures and utilities for Vigia Medical AI System.
Provides common mock objects, test data, and helper functions for all test suites.
"""

import pytest
import asyncio
import tempfile
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass
import uuid


# ============================================
# MEDICAL TEST DATA
# ============================================

@dataclass
class TestPatientData:
    """Test patient data structure."""
    patient_id: str
    name: str
    age: int
    medical_record: str
    diabetes: bool = False
    mobility_limited: bool = False
    braden_score: int = 15


TEST_PATIENTS = [
    TestPatientData("PAT-001", "César Durán", 75, "CD-2025-001", True, True, 12),
    TestPatientData("PAT-002", "María García", 68, "MG-2025-002", False, True, 14),
    TestPatientData("PAT-003", "Juan López", 82, "JL-2025-003", True, False, 10),
]

TEST_LPP_DETECTIONS = [
    {
        "lpp_grade": 1,
        "confidence": 0.85,
        "anatomical_location": "sacrum",
        "bounding_box": [100, 100, 200, 200],
        "risk_factors": ["diabetes", "limited_mobility"]
    },
    {
        "lpp_grade": 2,
        "confidence": 0.92,
        "anatomical_location": "heel",
        "bounding_box": [150, 150, 250, 250],
        "risk_factors": ["immobility", "poor_nutrition"]
    },
    {
        "lpp_grade": 3,
        "confidence": 0.88,
        "anatomical_location": "trochanter",
        "bounding_box": [80, 80, 180, 180],
        "risk_factors": ["infection", "tissue_necrosis"]
    }
]


# ============================================
# PYTEST FIXTURES
# ============================================

@pytest.fixture
def test_patient():
    """Provide a test patient."""
    return TEST_PATIENTS[0]


@pytest.fixture
def test_patients():
    """Provide multiple test patients."""
    return TEST_PATIENTS.copy()


@pytest.fixture
def test_lpp_detection():
    """Provide a test LPP detection."""
    return TEST_LPP_DETECTIONS[0].copy()


@pytest.fixture
def test_lpp_detections():
    """Provide multiple test LPP detections."""
    return [detection.copy() for detection in TEST_LPP_DETECTIONS]


@pytest.fixture
def temp_directory():
    """Provide a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_image_path(temp_directory):
    """Provide a mock test image path."""
    image_path = temp_directory / "test_lpp_image.jpg"
    # Create a minimal mock image file
    image_path.write_bytes(b"mock_image_data")
    return str(image_path)


@pytest.fixture
def sample_image_path(temp_directory):
    """Provide a sample image path for testing."""
    image_path = temp_directory / "sample_lpp_image.jpg"
    # Create a minimal mock image file
    image_path.write_bytes(b"mock_sample_image_data")
    return str(image_path)


@pytest.fixture
def session_id():
    """Provide a test session ID."""
    return f"test_session_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def patient_code():
    """Provide a test patient code."""
    return "CD-2025-001"


@pytest.fixture
def invalid_patient_codes():
    """Provide a list of invalid patient codes for testing."""
    return [
        "INVALID",
        "12345",
        "CD-XXXX-001",
        "CD-2025",
        "2025-001",
        "",
        None,
        "cd-2025-001",  # lowercase
        "CD-2025-0001",  # too many digits
        "XYZ-2025-001",  # invalid prefix
    ]


# ============================================
# MOCK OBJECTS
# ============================================

@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = AsyncMock()
    mock_client.create_detection = AsyncMock(return_value={"id": "det_123"})
    mock_client.create_clinical_note = AsyncMock(return_value={"id": "note_123"})
    mock_client.get_patient_history = AsyncMock(return_value=[])
    mock_client.initialize = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.get_cached_response = AsyncMock(return_value=None)
    mock_client.cache_response = AsyncMock(return_value=True)
    mock_client.search_medical_protocols = AsyncMock(return_value=[])
    mock_client.ping = AsyncMock(return_value=True)
    return mock_client


@pytest.fixture
def mock_lpp_detector():
    """Mock LPP detector for testing."""
    mock_detector = Mock()
    mock_detector.detect = Mock(return_value=[{
        "class_id": 2,
        "class_name": "grade2",
        "confidence": 0.85,
        "bbox": [100, 100, 200, 200],
        "location": "sacrum"
    }])
    return mock_detector


@pytest.fixture
def mock_image_preprocessor():
    """Mock image preprocessor for testing."""
    mock_preprocessor = Mock()
    mock_preprocessor.preprocess = Mock(return_value={
        "output_path": "/tmp/processed_image.jpg",
        "original_resolution": (1024, 768),
        "processed_resolution": (512, 384),
        "operations": ["resize", "normalize"]
    })
    mock_preprocessor.assess_quality = Mock(return_value={
        "overall_quality": 0.85,
        "sharpness": 0.9,
        "brightness": 0.8,
        "contrast": 0.85
    })
    return mock_preprocessor


@pytest.fixture
def mock_celery_app():
    """Mock Celery app for testing."""
    from vigia_detect.core.celery_mock import MockCelery
    return MockCelery()


@pytest.fixture
def mock_slack_client():
    """Mock Slack client for testing."""
    mock_client = AsyncMock()
    mock_client.chat_postMessage = AsyncMock(return_value={"ok": True, "ts": "1234567890.123456"})
    mock_client.views_open = AsyncMock(return_value={"ok": True})
    mock_client.views_update = AsyncMock(return_value={"ok": True})
    return mock_client


@pytest.fixture
def mock_twilio_client():
    """Mock Twilio client for testing."""
    mock_client = Mock()
    mock_message = Mock()
    mock_message.sid = "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    mock_client.messages.create = Mock(return_value=mock_message)
    return mock_client


# ============================================
# STANDARDIZED INPUT FIXTURES
# ============================================

@pytest.fixture
def standardized_input(session_id, patient_code):
    """Provide a standardized input for testing."""
    from vigia_detect.core.input_packager import StandardizedInput, InputSource, InputType
    
    return StandardizedInput(
        session_id=session_id,
        source=InputSource.WHATSAPP,
        input_type=InputType.MEDICAL_IMAGE,
        content=f"Patient code: {patient_code}. Medical image for LPP assessment.",
        metadata={
            "has_media": True,
            "media_type": "image/jpeg",
            "media_size": 512000,
            "phone_number": "+56987654321",
            "timestamp": datetime.now(timezone.utc).isoformat()
        },
        raw_content={
            "text": f"Patient code: {patient_code}. Medical image for LPP assessment.",
            "media_url": "https://example.com/test_image.jpg",
            "media_type": "image/jpeg",
            "media_size": 512000
        },
        security_context={
            "sanitized": True,
            "phi_detected": True,
            "safe_for_processing": True
        }
    )


@pytest.fixture 
def whatsapp_input_data():
    """Provide WhatsApp webhook input data."""
    return {
        "From": "whatsapp:+56987654321",
        "Body": "Patient CD-2025-001: New pressure injury detected on sacrum",
        "MediaUrl0": "https://api.twilio.com/test_image.jpg",
        "MediaContentType0": "image/jpeg",
        "MessageSid": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
        "AccountSid": "ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    }


@pytest.fixture
def slack_event_data():
    """Provide Slack event data for testing."""
    return {
        "type": "message",
        "channel": "C08KK1SRE5S",
        "user": "U12345678",
        "text": "Patient CD-2025-001: LPP Grade 2 detected",
        "ts": "1234567890.123456",
        "event_ts": "1234567890.123456"
    }


# ============================================
# MEDICAL DECISION FIXTURES
# ============================================

@pytest.fixture
def medical_decision_result():
    """Provide a medical decision result."""
    return {
        "lpp_grade": 2,
        "confidence": 0.85,
        "evidence_level": "A",
        "clinical_justification": "Clear evidence of partial thickness skin loss with exposed dermis",
        "recommendations": [
            "wound_dressing_hydrocolloid",
            "pressure_redistribution_surface",
            "pain_management"
        ],
        "escalation_required": False,
        "follow_up_hours": 48
    }


@pytest.fixture 
def minsal_compliance_data():
    """Provide MINSAL compliance test data."""
    return {
        "hospital_code": "HOS001",
        "region": "Metropolitana",
        "patient_rut": "12.345.678-9",
        "notification_required": True,
        "reporting_deadline_hours": 24
    }


# ============================================
# AGENT AND MCP FIXTURES
# ============================================

@pytest.fixture
def mock_adk_agent():
    """Mock ADK agent for testing."""
    from vigia_detect.agents.adk.base import VigiaBaseAgent
    mock_agent = Mock(spec=VigiaBaseAgent)
    mock_agent.agent_id = "test_agent"
    mock_agent.agent_name = "Test Medical Agent"
    mock_agent.process_request = AsyncMock(return_value={"success": True})
    return mock_agent


@pytest.fixture
def mock_mcp_gateway():
    """Mock MCP gateway for testing."""
    mock_gateway = AsyncMock()
    mock_gateway.whatsapp_operation = AsyncMock(return_value={"success": True})
    mock_gateway.slack_operation = AsyncMock(return_value={"success": True})
    mock_gateway.cache_patient_data = AsyncMock(return_value=True)
    mock_gateway.search_medical_protocols = AsyncMock(return_value=[])
    return mock_gateway


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_mock_detection_result(lpp_grade: int = 2, confidence: float = 0.85):
    """Create a mock detection result."""
    from vigia_detect.systems.clinical_processing import ClinicalDetection, LPPGrade
    
    return ClinicalDetection(
        detected=True,
        lpp_grade=LPPGrade(lpp_grade),
        confidence=confidence,
        bounding_boxes=[[100, 100, 200, 200]],
        clinical_features={
            "location": "sacrum",
            "size_category": "medium",
            "tissue_involvement": "dermis"
        },
        risk_factors=["diabetes", "limited_mobility"],
        recommended_interventions=[
            "wound_dressing_hydrocolloid",
            "pressure_redistribution_surface"
        ],
        measurement_data={
            "width_cm": 3.5,
            "height_cm": 2.8,
            "area_cm2": 9.8
        }
    )


def create_mock_clinical_report(session_id: str, patient_code: str):
    """Create a mock clinical report."""
    from vigia_detect.systems.clinical_processing import ClinicalReport
    
    return ClinicalReport(
        session_id=session_id,
        patient_code=patient_code,
        detection_result=create_mock_detection_result(),
        processing_time=2.35,
        image_metadata={"quality_metrics": {"overall_quality": 0.85}},
        clinical_notes="Grade 2 LPP detected with high confidence",
        quality_metrics={
            "image_quality": 0.85,
            "detection_confidence": 0.85,
            "documentation_score": 0.92
        },
        compliance_flags=["confidence_threshold_met", "interventions_documented"],
        timestamp=datetime.now(timezone.utc),
        processor_version="1.0.0"
    )


class MockAsyncContext:
    """Mock async context manager for testing."""
    
    def __init__(self, return_value=None):
        self.return_value = return_value
        
    async def __aenter__(self):
        return self.return_value or Mock()
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# ============================================
# ASSERTION HELPERS
# ============================================

def assert_medical_compliance(result: Dict[str, Any]):
    """Assert that a result meets medical compliance requirements."""
    assert "session_id" in result
    assert "patient_code" in result or "patient_id" in result
    assert "timestamp" in result or "created_at" in result
    assert "compliance_flags" in result or "medical_compliance" in result


def assert_lpp_detection_valid(detection: Dict[str, Any]):
    """Assert that an LPP detection result is valid."""
    assert "detected" in detection
    assert "confidence" in detection
    if detection["detected"]:
        assert "lpp_grade" in detection
        assert detection["confidence"] >= 0.0
        assert detection["confidence"] <= 1.0
        assert detection["lpp_grade"] in [1, 2, 3, 4, 5, 6]


def assert_agent_response_valid(response: Dict[str, Any]):
    """Assert that an agent response is valid."""
    assert "success" in response or "status" in response
    assert "timestamp" in response or "created_at" in response
    if "success" in response and response["success"]:
        assert "data" in response or "result" in response


# ============================================
# EXPORT ALL FIXTURES
# ============================================

__all__ = [
    # Test data
    'TestPatientData', 'TEST_PATIENTS', 'TEST_LPP_DETECTIONS',
    
    # Basic fixtures
    'test_patient', 'test_patients', 'test_lpp_detection', 'test_lpp_detections',
    'temp_directory', 'test_image_path', 'sample_image_path', 'session_id', 'patient_code', 'invalid_patient_codes',
    
    # Mock objects
    'mock_supabase_client', 'mock_redis_client', 'mock_lpp_detector',
    'mock_image_preprocessor', 'mock_celery_app', 'mock_slack_client', 'mock_twilio_client',
    
    # Input fixtures
    'standardized_input', 'whatsapp_input_data', 'slack_event_data',
    
    # Medical fixtures
    'medical_decision_result', 'minsal_compliance_data',
    
    # Agent fixtures
    'mock_adk_agent', 'mock_mcp_gateway',
    
    # Utility functions
    'create_mock_detection_result', 'create_mock_clinical_report', 'MockAsyncContext',
    
    # Assertion helpers
    'assert_medical_compliance', 'assert_lpp_detection_valid', 'assert_agent_response_valid'
]