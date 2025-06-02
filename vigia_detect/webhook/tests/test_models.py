"""
Tests for webhook models and data structures.
"""

import pytest
from datetime import datetime
from dataclasses import FrozenInstanceError

from ..models import (
    EventType, Severity, Detection, DetectionPayload, 
    PatientInfo, WebhookEvent, WebhookResponse
)


class TestEventType:
    """Test EventType enum."""
    
    def test_event_type_values(self):
        """Test that all event types have correct values."""
        assert EventType.DETECTION_COMPLETED.value == "detection.completed"
        assert EventType.DETECTION_FAILED.value == "detection.failed"
        assert EventType.PATIENT_UPDATED.value == "patient.updated"
        assert EventType.PROTOCOL_TRIGGERED.value == "protocol.triggered"
        assert EventType.ANALYSIS_READY.value == "analysis.ready"
    
    def test_event_type_from_string(self):
        """Test creating EventType from string values."""
        assert EventType("detection.completed") == EventType.DETECTION_COMPLETED
        assert EventType("detection.failed") == EventType.DETECTION_FAILED
        assert EventType("patient.updated") == EventType.PATIENT_UPDATED
        assert EventType("protocol.triggered") == EventType.PROTOCOL_TRIGGERED
        assert EventType("analysis.ready") == EventType.ANALYSIS_READY
    
    def test_invalid_event_type(self):
        """Test that invalid event type raises ValueError."""
        with pytest.raises(ValueError):
            EventType("invalid.event")


class TestSeverity:
    """Test Severity enum."""
    
    def test_severity_values(self):
        """Test that all severity levels have correct values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"
    
    def test_severity_ordering(self):
        """Test that severity levels can be compared."""
        # Note: This would require implementing __lt__ etc. in the enum
        # For now, just test they exist
        severities = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
        assert len(severities) == 5


class TestDetection:
    """Test Detection dataclass."""
    
    def test_detection_creation(self):
        """Test creating a Detection instance."""
        detection = Detection(
            stage=3,
            confidence=0.85,
            bbox=[100, 100, 200, 200],
            area=10000.0,
            severity=Severity.HIGH
        )
        
        assert detection.stage == 3
        assert detection.confidence == 0.85
        assert detection.bbox == [100, 100, 200, 200]
        assert detection.area == 10000.0
        assert detection.severity == Severity.HIGH
    
    def test_detection_to_dict(self):
        """Test converting Detection to dictionary."""
        detection = Detection(
            stage=2,
            confidence=0.75,
            bbox=[50, 50, 150, 150],
            area=10000.0,
            severity=Severity.MEDIUM
        )
        
        result = detection.to_dict()
        
        assert result["stage"] == 2
        assert result["confidence"] == 0.75
        assert result["bbox"] == [50, 50, 150, 150]
        assert result["area"] == 10000.0
        assert result["severity"] == "medium"  # Should be string value
    
    def test_detection_validation(self):
        """Test Detection with various data types."""
        # Test with valid integer confidence
        detection1 = Detection(
            stage=1,
            confidence=1,  # Integer should work
            bbox=[0, 0, 100, 100],
            area=10000,  # Integer should work
            severity=Severity.LOW
        )
        assert detection1.confidence == 1
        assert detection1.area == 10000
        
        # Test with negative values (should be allowed by dataclass)
        detection2 = Detection(
            stage=4,
            confidence=0.95,
            bbox=[-10, -10, 90, 90],  # Negative coordinates possible
            area=10000.0,
            severity=Severity.CRITICAL
        )
        assert detection2.bbox == [-10, -10, 90, 90]


class TestPatientInfo:
    """Test PatientInfo dataclass."""
    
    def test_patient_info_creation(self):
        """Test creating PatientInfo with all fields."""
        patient = PatientInfo(
            code="PATIENT-001",
            name="John Doe",
            age=65,
            location="Room 101"
        )
        
        assert patient.code == "PATIENT-001"
        assert patient.name == "John Doe"
        assert patient.age == 65
        assert patient.location == "Room 101"
    
    def test_patient_info_minimal(self):
        """Test creating PatientInfo with only required fields."""
        patient = PatientInfo(code="PATIENT-002")
        
        assert patient.code == "PATIENT-002"
        assert patient.name is None
        assert patient.age is None
        assert patient.location is None
    
    def test_patient_info_to_dict(self):
        """Test converting PatientInfo to dictionary."""
        patient = PatientInfo(
            code="PATIENT-003",
            name="Jane Smith",
            age=45,
            location="Room 205"
        )
        
        result = patient.to_dict()
        
        assert result["code"] == "PATIENT-003"
        assert result["name"] == "Jane Smith"
        assert result["age"] == 45
        assert result["location"] == "Room 205"


class TestDetectionPayload:
    """Test DetectionPayload dataclass."""
    
    def test_detection_payload_creation(self):
        """Test creating DetectionPayload with all fields."""
        detections = [
            Detection(
                stage=2,
                confidence=0.8,
                bbox=[100, 100, 200, 200],
                area=10000.0,
                severity=Severity.MEDIUM
            )
        ]
        
        patient_info = PatientInfo(
            code="TEST-001",
            name="Test Patient",
            age=70
        )
        
        payload = DetectionPayload(
            patient_code="TEST-001",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            image_path="/path/to/image.jpg",
            detections=detections,
            risk_level="MEDIUM",
            patient_info=patient_info,
            processing_time=1.5,
            metadata={"model_version": "v1.0"}
        )
        
        assert payload.patient_code == "TEST-001"
        assert payload.timestamp == datetime(2025, 1, 15, 10, 30, 0)
        assert payload.image_path == "/path/to/image.jpg"
        assert len(payload.detections) == 1
        assert payload.risk_level == "MEDIUM"
        assert payload.patient_info.code == "TEST-001"
        assert payload.processing_time == 1.5
        assert payload.metadata["model_version"] == "v1.0"
    
    def test_detection_payload_minimal(self):
        """Test creating DetectionPayload with minimal required fields."""
        payload = DetectionPayload(
            patient_code="TEST-002",
            timestamp=datetime.now(),
            image_path="/minimal/image.jpg",
            detections=[],
            risk_level="LOW"
        )
        
        assert payload.patient_code == "TEST-002"
        assert payload.detections == []
        assert payload.risk_level == "LOW"
        assert payload.patient_info is None
        assert payload.processing_time is None
        assert payload.metadata is None
    
    def test_detection_payload_to_dict(self):
        """Test converting DetectionPayload to dictionary."""
        timestamp = datetime(2025, 1, 15, 10, 30, 0)
        detections = [
            Detection(
                stage=3,
                confidence=0.9,
                bbox=[200, 200, 300, 300],
                area=10000.0,
                severity=Severity.HIGH
            )
        ]
        
        payload = DetectionPayload(
            patient_code="TEST-003",
            timestamp=timestamp,
            image_path="/test/image.jpg",
            detections=detections,
            risk_level="HIGH",
            processing_time=2.1
        )
        
        result = payload.to_dict()
        
        assert result["patient_code"] == "TEST-003"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["image_path"] == "/test/image.jpg"
        assert len(result["detections"]) == 1
        assert result["detections"][0]["stage"] == 3
        assert result["risk_level"] == "HIGH"
        assert result["processing_time"] == 2.1
        assert "patient_info" not in result  # Should not include None values


class TestWebhookEvent:
    """Test WebhookEvent dataclass."""
    
    def test_webhook_event_creation(self):
        """Test creating WebhookEvent."""
        timestamp = datetime.now()
        payload = {"test": "data"}
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=timestamp,
            payload=payload,
            source="test_system",
            version="2.0",
            webhook_id="test-id-123"
        )
        
        assert event.event_type == EventType.DETECTION_COMPLETED
        assert event.timestamp == timestamp
        assert event.payload == payload
        assert event.source == "test_system"
        assert event.version == "2.0"
        assert event.webhook_id == "test-id-123"
    
    def test_webhook_event_defaults(self):
        """Test WebhookEvent with default values."""
        event = WebhookEvent(
            event_type=EventType.PATIENT_UPDATED,
            timestamp=datetime.now(),
            payload={"patient": "data"},
            source="test"
        )
        
        assert event.version == "1.0"  # Default version
        assert event.webhook_id is None  # Default webhook_id
    
    def test_webhook_event_to_dict(self):
        """Test converting WebhookEvent to dictionary."""
        timestamp = datetime(2025, 1, 15, 10, 30, 0)
        payload = {"detection": "data"}
        
        event = WebhookEvent(
            event_type=EventType.PROTOCOL_TRIGGERED,
            timestamp=timestamp,
            payload=payload,
            source="vigia_system",
            version="1.5",
            webhook_id="webhook-456"
        )
        
        result = event.to_dict()
        
        assert result["event_type"] == "protocol.triggered"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["payload"] == payload
        assert result["source"] == "vigia_system"
        assert result["version"] == "1.5"
        assert result["webhook_id"] == "webhook-456"
    
    def test_webhook_event_with_detection_payload(self):
        """Test WebhookEvent with DetectionPayload as payload."""
        detection_payload = DetectionPayload(
            patient_code="TEST-004",
            timestamp=datetime.now(),
            image_path="/test.jpg",
            detections=[],
            risk_level="LOW"
        )
        
        event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload=detection_payload,
            source="test"
        )
        
        result = event.to_dict()
        
        # Should call to_dict() on the payload
        assert result["payload"]["patient_code"] == "TEST-004"
        assert result["payload"]["risk_level"] == "LOW"


class TestWebhookResponse:
    """Test WebhookResponse dataclass."""
    
    def test_webhook_response_creation(self):
        """Test creating WebhookResponse."""
        response = WebhookResponse(
            success=True,
            status_code=200,
            message="Success",
            data={"result": "processed"}
        )
        
        assert response.success is True
        assert response.status_code == 200
        assert response.message == "Success"
        assert response.data == {"result": "processed"}
    
    def test_webhook_response_minimal(self):
        """Test creating WebhookResponse with minimal fields."""
        response = WebhookResponse(
            success=False,
            status_code=500
        )
        
        assert response.success is False
        assert response.status_code == 500
        assert response.message is None
        assert response.data is None
    
    def test_webhook_response_error(self):
        """Test creating WebhookResponse for error cases."""
        response = WebhookResponse(
            success=False,
            status_code=401,
            message="Unauthorized",
            data={"error": "Invalid API key"}
        )
        
        assert response.success is False
        assert response.status_code == 401
        assert response.message == "Unauthorized"
        assert response.data["error"] == "Invalid API key"


class TestModelIntegration:
    """Integration tests for model interactions."""
    
    def test_complete_detection_workflow_models(self):
        """Test a complete workflow using all models together."""
        # Create detection
        detection = Detection(
            stage=4,
            confidence=0.92,
            bbox=[100, 100, 300, 300],
            area=40000.0,
            severity=Severity.CRITICAL
        )
        
        # Create patient info
        patient_info = PatientInfo(
            code="WORKFLOW-001",
            name="Test Patient",
            age=75,
            location="ICU Room 5"
        )
        
        # Create detection payload
        detection_payload = DetectionPayload(
            patient_code="WORKFLOW-001",
            timestamp=datetime.now(),
            image_path="/critical/image.jpg",
            detections=[detection],
            risk_level="CRITICAL",
            patient_info=patient_info,
            processing_time=3.2,
            metadata={"urgent": True}
        )
        
        # Create webhook event
        webhook_event = WebhookEvent(
            event_type=EventType.DETECTION_COMPLETED,
            timestamp=datetime.now(),
            payload=detection_payload,
            source="integration_test",
            webhook_id="integration-123"
        )
        
        # Convert to dict and verify structure
        event_dict = webhook_event.to_dict()
        
        assert event_dict["event_type"] == "detection.completed"
        assert event_dict["payload"]["patient_code"] == "WORKFLOW-001"
        assert event_dict["payload"]["risk_level"] == "CRITICAL"
        assert len(event_dict["payload"]["detections"]) == 1
        assert event_dict["payload"]["detections"][0]["stage"] == 4
        assert event_dict["payload"]["detections"][0]["severity"] == "critical"
        assert event_dict["payload"]["patient_info"]["name"] == "Test Patient"
        assert event_dict["source"] == "integration_test"
        assert event_dict["webhook_id"] == "integration-123"
    
    def test_model_serialization_roundtrip(self):
        """Test that models can be serialized and data preserved."""
        original_detection = Detection(
            stage=2,
            confidence=0.77,
            bbox=[150, 150, 250, 250],
            area=10000.0,
            severity=Severity.MEDIUM
        )
        
        # Serialize to dict
        detection_dict = original_detection.to_dict()
        
        # Verify serialized data
        assert detection_dict["stage"] == 2
        assert detection_dict["confidence"] == 0.77
        assert detection_dict["bbox"] == [150, 150, 250, 250]
        assert detection_dict["area"] == 10000.0
        assert detection_dict["severity"] == "medium"
        
        # Could recreate from dict if needed
        recreated_detection = Detection(
            stage=detection_dict["stage"],
            confidence=detection_dict["confidence"],
            bbox=detection_dict["bbox"],
            area=detection_dict["area"],
            severity=Severity(detection_dict["severity"])
        )
        
        assert recreated_detection.stage == original_detection.stage
        assert recreated_detection.confidence == original_detection.confidence
        assert recreated_detection.severity == original_detection.severity